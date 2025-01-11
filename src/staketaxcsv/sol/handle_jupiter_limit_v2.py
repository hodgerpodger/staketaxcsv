import logging

from staketaxcsv.common.ExporterTypes import TX_TYPE_SOL_JUPITER_LIMIT_OPEN
from staketaxcsv.common.make_tx import make_swap_tx, make_simple_tx, make_spend_fee_tx
from staketaxcsv.sol.constants import CURRENCY_SOL
from staketaxcsv.sol.handle_jupiter_dca import _get_sol_transfer_amount


class LimitOrder:

    orders = {}   # <order_id> -> <dict_of_order_info>

    def open(self, txinfo_init_order):
        inner_parsed = txinfo_init_order.inner_parsed
        transfers_in, transfers_out, _ = txinfo_init_order.transfers
        net_transfers_in, net_transfers_out, _ = txinfo_init_order.transfers_net

        # To ID the limit order, use contract token account that receives sent currency (i.e. ORCA, etc.)
        limit_order_id = inner_parsed["initializeAccount3"][-1]["account"]

        # Find sol deposit amount
        amount_sol_deposit = _get_sol_transfer_amount(transfers_out)
        assert (amount_sol_deposit is not None)

        # Find sent amount/currency for limit order
        assert (len(net_transfers_out) == 1)
        sent_amount, sent_currency, _, _ = net_transfers_out[0]

        LimitOrder.orders[limit_order_id] = {
            "amount_sol_deposit": amount_sol_deposit,
            "sent_amount": sent_amount,
            "sent_currency": sent_currency,
        }

        return limit_order_id, amount_sol_deposit, sent_amount, sent_currency

    def route(self, txinfo):
        transfers_in, transfers_out, _ = txinfo.transfers_net
        inner_parsed = txinfo.inner_parsed
        mints = txinfo.mints
        balance_changes_all = txinfo.balance_changes_all

        # Identify limit_order_id just for info purposes
        token_accounts = set(balance_changes_all.keys()) & set(LimitOrder.orders.keys())
        if len(token_accounts) == 1:
            limit_order_id = list(token_accounts)[0]
        else:
            limit_order_id = "unknown"

        # Find sent amount/currency (technically withdrawn from contract token account)
        if "transferChecked" in inner_parsed:
            transfers_list = inner_parsed["transferChecked"]
            sent_amount = transfers_list[0]["tokenAmount"]["uiAmount"]
            sent_mint = transfers_list[0]["mint"]
            sent_currency = mints[sent_mint]["currency"]

        # Get received amount/currency from user wallet balance change
        if len(transfers_in) == 1:
            # Non-last tx in limit order series
            received_amount, received_currency, _, _ = transfers_in[0]
        elif len(transfers_in) == 2:
            # Last tx in limit order series (remaining SOL deposit minus fee is returned)
            amount_sol_refund, received_amount, received_currency = self._received_amounts(transfers_in)

        return limit_order_id, sent_amount, sent_currency, received_amount, received_currency

    def cancel(self, txinfo):
        inner_parsed = txinfo.inner_parsed
        transfers_in, transfers_out, _ = txinfo.transfers_net

        limit_order_id = inner_parsed["closeAccount"][0]["account"]

        # Get amount_sol_deposit (lookup original limit order)
        amount_sol_deposit = None
        if limit_order_id in LimitOrder.orders:
            amount_sol_deposit = LimitOrder.orders[limit_order_id]["amount_sol_deposit"]

        # Get amount_sol_refund (use net incoming transfers)
        amount_sol_refund, received_amount, received_currency = self._received_amounts(transfers_in)

        # Calculate SOL fee of limit order series: fee = deposit - refund
        if amount_sol_deposit and amount_sol_refund:
            amount_sol_fee = amount_sol_deposit - amount_sol_refund
            self._fee_sanity_check(amount_sol_fee)
        else:
            # Default to zero when unable to calculate sol fee
            amount_sol_fee = 0

        return limit_order_id, amount_sol_fee, amount_sol_refund, received_amount, received_currency

    def _fee_sanity_check(self, amount_sol_fee):
        if amount_sol_fee > 0.5:
            raise Exception("Bad value for amount_sol_fee={}".format(amount_sol_fee))

    def _received_amounts(self, transfers_in):
        # Only SOL received case
        if len(transfers_in) == 1 and transfers_in[0][1] == CURRENCY_SOL:
            amt, cur, _, _ = transfers_in[0]
            return amt, amt, cur

        # Other tokens case
        assert (len(transfers_in) == 2)
        amount_sol_refund = None
        received_currency = None

        for amt, cur, _, _ in transfers_in:
            if cur == CURRENCY_SOL:
                amount_sol_refund = amt
            else:
                received_amount = amt
                received_currency = cur

        return amount_sol_refund, received_amount, received_currency


def handle_jupiter_limit_v2(exporter, txinfo):
    txinfo.comment = "jupiter_limit_v2"
    log_instructions = txinfo.log_instructions
    transfers_in, transfers_out, _ = txinfo.transfers_net

    if "Route" in log_instructions or "SharedAccountsRoute" in log_instructions:
        _handle_route(exporter, txinfo)
    elif "InitializeOrder" in log_instructions:
        _handle_open(exporter, txinfo)
    elif "CancelOrder" in log_instructions:
        _handle_cancel(exporter, txinfo)
    else:
        raise Exception("Unable to handle tx in handle_jupiter_limit()")


def _handle_open(exporter, txinfo):
    txinfo.comment += ".open"

    limit_order_id, amount_sol_deposit, sent_amount, sent_currency = LimitOrder().open(txinfo)

    txinfo.comment += f" [limit_order_id={limit_order_id[:6]}]"
    txinfo.comment += f" [sent {sent_amount} {sent_currency} and {amount_sol_deposit} SOL (fee deposit)]"

    # Ignore transfer of SOL since SOL deposit is returned at end of limit order series (minus fees)
    row = make_simple_tx(txinfo, TX_TYPE_SOL_JUPITER_LIMIT_OPEN)
    row.fee = ""
    row.fee_currency = ""
    exporter.ingest_row(row)


def _handle_route(exporter, txinfo):
    txinfo.comment += ".route_execute_order"

    limit_order_id, sent_amount, sent_currency, received_amount, received_currency = LimitOrder().route(txinfo)

    txinfo.comment += f" [limit_order_id={limit_order_id[:6]}]"
    txinfo.comment += f" [received {received_amount} {received_currency}]"

    row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    exporter.ingest_row(row)


def _handle_cancel(exporter, txinfo):
    txinfo.comment += ".cancel"

    limit_order_id, amount_sol_fee, amount_sol_refund, received_amount, received_currency = LimitOrder().cancel(txinfo)

    txinfo.comment += f" [limit_order_id={limit_order_id[:6]}]"
    txinfo.comment += f" [received {received_amount} {received_currency} and {amount_sol_refund} SOL (fee deposit returned)]"

    row = make_spend_fee_tx(txinfo, amount_sol_fee, CURRENCY_SOL)
    row.fee = ""
    row.fee_currency = ""
    exporter.ingest_row(row)
