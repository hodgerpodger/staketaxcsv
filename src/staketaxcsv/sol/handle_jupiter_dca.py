import logging

from staketaxcsv.common.make_tx import make_swap_tx, make_simple_tx, make_spend_fee_tx
from staketaxcsv.common.ExporterTypes import TX_TYPE_SOL_JUPITER_OPEN_DCA
from staketaxcsv.sol.handle_simple import handle_unknown_detect_transfers
from staketaxcsv.sol.constants import CURRENCY_SOL


class DcaSeries:

    sol_deposits = {}  # <dca_order_id> -> <amount_sol_deposit>

    def open(self, txinfo_open_dca):
        """ On open dca order, saves sol amount deposited for fees """
        inner_parsed = txinfo_open_dca.inner_parsed
        transfers_in, transfers_out, _ = txinfo_open_dca.transfers

        # Use contract wallet that receives funds for fee to ID the dca order
        wallet_sol_deposit = inner_parsed["create"][0]["wallet"]

        # Find sol deposit amount
        amount_sol_deposit = None
        for amt, cur, _, _ in transfers_out:
            if cur == CURRENCY_SOL:
                amount_sol_deposit = amt
        assert (amount_sol_deposit is not None)

        DcaSeries.sol_deposits[wallet_sol_deposit] = amount_sol_deposit

    def close(self, txinfo_close_dca):
        """ On close dca order, returns sol fee amount (fee = deposit - refund) """
        inner_parsed = txinfo_close_dca.inner_parsed
        transfers_in, transfers_out, _ = txinfo_close_dca.transfers_net

        # Lookup sol deposit for this dca order
        wallet_sol_deposit = inner_parsed["closeAccount"][0]["owner"]
        amount_sol_deposit = DcaSeries.sol_deposits.get(wallet_sol_deposit, None)

        # Find sol refund amount
        amount_sol_refund = None
        for amt, cur, _, _ in transfers_in:
            if cur == CURRENCY_SOL:
                amount_sol_refund = amt
        assert (amount_sol_refund is not None)

        logging.info("wallet_sol_deposit:%s, amount_sol_deposit: %s, amount_sol_refund:%s",
                     wallet_sol_deposit, amount_sol_deposit, amount_sol_refund)

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

    if "OpenDca" in txinfo.log_instructions:
        # open dca order tx
        _handle_open_dca(exporter, txinfo)
        return
    elif ("SharedAccountsRoute" in txinfo.log_instructions
          and "EndAndClose" in txinfo.log_instructions):
        # last swap + close dca order tx
        _handle_close_dca(exporter, txinfo)
        return
    elif "SharedAccountsRoute" in txinfo.log_instructions:
        # not-last swap tx
        txinfo.comment += ".swap"
        _handle_swap(exporter, txinfo)
        return
    else:
        logging.error("Unknown log_instructions")

    handle_unknown_detect_transfers(exporter, txinfo)


def _handle_open_dca(exporter, txinfo):
    txinfo.comment += ".open_dca"

    # Ignore transfer of SOL since SOL deposit is returned at end of dca order (minus fees)
    row = make_simple_tx(txinfo, TX_TYPE_SOL_JUPITER_OPEN_DCA)
    row.fee = ""
    row.fee_currency = ""
    exporter.ingest_row(row)

    DcaSeries().open(txinfo)


def _handle_close_dca(exporter, txinfo):
    txinfo.comment += ".swap_and_close_dca"

    # report swap tx
    _handle_swap(exporter, txinfo)

    # determine sol fee for entire dca order series (fee = deposit - refund)
    amount_sol = DcaSeries().close(txinfo)

    # report spend fee tx
    if amount_sol:
        row = make_spend_fee_tx(txinfo, amount_sol, CURRENCY_SOL)
        row.fee = ""
        row.fee_currency = ""
        row.comment += " [SOL fee for dca order (deposit - refund)]"
        exporter.ingest_row(row)


def _handle_swap(exporter, txinfo):
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

        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return True

    logging.error("Unable to handle jupiter dca swap in _handle_swap()")
    return False


def _amt_currency(txinfo, transfer_checked):
    amount = transfer_checked["tokenAmount"]["uiAmount"]
    currency = txinfo.mints[transfer_checked["mint"]]["currency"]
    return amount, currency
