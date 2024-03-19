import logging

from staketaxcsv.common.make_tx import make_swap_tx, make_simple_tx, make_spend_fee_tx
from staketaxcsv.common.ExporterTypes import TX_TYPE_SOL_JUPITER_DCA_OPEN, TX_TYPE_SOL_JUPITER_DCA_CLOSE
from staketaxcsv.sol.handle_simple import handle_unknown_detect_transfers
from staketaxcsv.sol.constants import CURRENCY_SOL

SHARED_ACCOUNTS_ROUTE = "SharedAccountsRoute"
OPEN_DCA = "OpenDca"
OPEN_DCA_V2 = "OpenDcaV2"
ROUTE = "Route"
END_AND_CLOSE = "EndAndClose"
CLOSE_DCA = "CloseDca"


class DcaSeries:

    sol_deposits = {}  # <dca_order_id> -> <amount_sol_deposit>

    def open(self, txinfo_open_dca):
        """ On open dca order, saves sol amount deposited for fees """
        inner_parsed = txinfo_open_dca.inner_parsed
        transfers_in, transfers_out, _ = txinfo_open_dca.transfers

        # Use contract wallet that receives funds for fee to ID the dca order
        dca_order_id = inner_parsed["create"][0]["wallet"]

        # Find sol deposit amount
        amount_sol_deposit = _get_sol_transfer_amount(transfers_out)
        assert (amount_sol_deposit is not None)

        DcaSeries.sol_deposits[dca_order_id] = amount_sol_deposit

    def close(self, txinfo_close_dca):
        """ On close dca order, returns sol fee amount (fee = deposit - refund) """
        inner_parsed = txinfo_close_dca.inner_parsed
        transfers_in, transfers_out, _ = txinfo_close_dca.transfers_net

        dca_order_id = inner_parsed["closeAccount"][0]["owner"]

        # Lookup sol deposit for this dca order
        amount_sol_deposit = DcaSeries.sol_deposits.get(dca_order_id, None)

        # Find sol refund amount
        amount_sol_refund = _get_sol_transfer_amount(transfers_in)
        assert (amount_sol_refund is not None)

        logging.info("dca_order_id:%s, amount_sol_deposit: %s, amount_sol_refund:%s",
                     dca_order_id, amount_sol_deposit, amount_sol_refund)

        if amount_sol_deposit and amount_sol_refund:
            fee_series = amount_sol_deposit - amount_sol_refund
            # sanity check
            if 0 < fee_series < 0.5:
                return fee_series
            logging.error("bad value for fee_series:%s", fee_series)
        return None


def handle_jupiter_dca(exporter, txinfo):
    txinfo.comment = "jupiter_dca"
    transfers_in, transfers_out, _ = txinfo.transfers_net

    if (OPEN_DCA in txinfo.log_instructions or OPEN_DCA_V2 in txinfo.log_instructions):
        # open dca order tx
        txinfo.comment += ".open_dca"
        _handle_open_dca(exporter, txinfo)
        return
    elif (SHARED_ACCOUNTS_ROUTE in txinfo.log_instructions
          and (END_AND_CLOSE in txinfo.log_instructions or CLOSE_DCA in txinfo.log_instructions)):
        # last swap + close dca order tx ('SharedAccountsRoute' instruction)
        txinfo.comment += ".swap_and_close_dca.shared"
        _handle_swap_shared_accounts_route(exporter, txinfo)
        _handle_close_dca(exporter, txinfo)
        return
    elif SHARED_ACCOUNTS_ROUTE in txinfo.log_instructions:
        # not-last swap tx ('SharedAccountsRoute' instruction)
        txinfo.comment += ".swap.shared"
        _handle_swap_shared_accounts_route(exporter, txinfo)
        return
    elif (ROUTE in txinfo.log_instructions
          and (END_AND_CLOSE in txinfo.log_instructions or CLOSE_DCA in txinfo.log_instructions)):
        # last swap + close dca order tx ('Route' instruction)
        txinfo.comment += ".swap_and_close_dca.route"
        _handle_swap_route(exporter, txinfo)
        _handle_close_dca(exporter, txinfo)
        return
    elif ROUTE in txinfo.log_instructions:
        # not-last swap tx ('Route' instruction)
        txinfo.comment += ".swap.route"
        _handle_swap_route(exporter, txinfo)
        return
    elif END_AND_CLOSE in txinfo.log_instructions or CLOSE_DCA in txinfo.log_instructions:
        txinfo.comment += ".close_dca"
        _handle_close_dca(exporter, txinfo)
    else:
        logging.error("Unknown log_instructions")
        handle_unknown_detect_transfers(exporter, txinfo)


def _handle_open_dca(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers_net

    # Ignore transfer of SOL since SOL deposit is returned at end of dca order (minus fees)
    row = make_simple_tx(txinfo, TX_TYPE_SOL_JUPITER_DCA_OPEN)
    row.fee = ""
    row.fee_currency = ""

    # Add comment on amount deposited for dca order
    for amt, cur, _, _ in transfers_out:
        if cur != CURRENCY_SOL:
            row.comment += f" [{amt} {cur} deposited]"

    exporter.ingest_row(row)

    DcaSeries().open(txinfo)


def _handle_close_dca(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers_net

    # determine sol fee for entire dca order series (fee = deposit - refund)
    amount_sol = DcaSeries().close(txinfo)

    if amount_sol:
        # report as spend fee tx
        row = make_spend_fee_tx(txinfo, amount_sol, CURRENCY_SOL)
        row.fee = ""
        row.fee_currency = ""
        row.comment += " [SOL fee = deposit - refund]"
    else:
        row = make_simple_tx(txinfo, TX_TYPE_SOL_JUPITER_DCA_CLOSE)

    # Add comment on amount returned for dca order
    for amt, cur, _, _ in transfers_in:
        if cur != CURRENCY_SOL:
            row.comment += f" [{amt} {cur} returned]"

    exporter.ingest_row(row)


def _handle_swap_route(exporter, txinfo):
    # swap tx with 'Route' instruction
    transfers_in, transfers_out, _ = txinfo.transfers_net
    inner_parsed = txinfo.inner_parsed
    account_to_mint = txinfo.account_to_mint
    mints = txinfo.mints

    if "transfer" in inner_parsed:
        transfers_list = inner_parsed["transfer"]

        # receive amount/currency from transfers_in
        received_amount, received_currency, _, _ = transfers_in[0]
        assert (len(transfers_in) == 1)

        # sent amount/currency from instruction's transfer data
        sent_amount_raw = transfers_list[0]["amount"]
        destination = transfers_list[0]["destination"]
        sent_mint = account_to_mint[destination]
        sent_currency = mints[sent_mint]["currency"]
        sent_amount = float(sent_amount_raw) / (10**mints[sent_mint]["decimals"])

        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return True

    logging.error("Unable to handle jupiter dca swap in _handle_swap_route()")
    return False


def _handle_swap_shared_accounts_route(exporter, txinfo):
    # swap tx with 'SharedAccountsRoute' instruction
    transfers_in, transfers_out, _ = txinfo.transfers_net
    inner_parsed = txinfo.inner_parsed

    if "transferChecked" in inner_parsed:
        # Get sent amt/currency, receive currency from instruction
        transfers_list = inner_parsed["transferChecked"]

        # 1st transfer is sent currency
        sent_amount, sent_currency = _amt_currency(txinfo, transfers_list[0])

        # may be some middle intermediate transfers

        # last transfer is received currency (may include extra fee that contract actually takes)
        received_amount_with_fee, received_currency = _amt_currency(txinfo, transfers_list[-1])

        # For receive amount, look at "transfers_in" first if exists (because it has fee deduction)
        received_amount = None
        if len(transfers_in) > 0:
            for amt, cur, _, _ in transfers_in:
                if cur == received_currency:
                    received_amount = amt
        if received_amount is None:
            received_amount = received_amount_with_fee

        # If swap involves SOL sent out, make sure SOL fee is zeroed to avoid error in special case of SOL.
        if sent_currency == CURRENCY_SOL:
            txinfo.fee = ""
            txinfo.fee_currency = ""

        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return True

    logging.error("Unable to handle jupiter dca swap in _handle_swap_shared_accounts_route()")
    return False


def _amt_currency(txinfo, transfer_checked):
    amount = transfer_checked["tokenAmount"]["uiAmount"]
    currency = txinfo.mints[transfer_checked["mint"]]["currency"]
    return amount, currency


def _get_sol_transfer_amount(transfers_list):
    for amt, cur, _, _ in transfers_list:
        if cur == CURRENCY_SOL:
            return amt
    return None
