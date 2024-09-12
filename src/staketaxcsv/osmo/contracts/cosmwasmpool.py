import logging
import math
from staketaxcsv.common.make_tx import make_spend_fee_tx
from staketaxcsv.osmo.make_tx import make_osmo_swap_tx
from staketaxcsv.osmo import denoms
from staketaxcsv.settings_csv import OSMO_NODE
from staketaxcsv.osmo import util_osmo


class LimitOrders:

    def claim(self, wasm_limit_claimed, wallet_address):
        """ Reads claim transaction ('batch claim or claim limit') and returns list of trades executed

        :param wasm_limit_claimed: "wasm-limitClaimed" element dictionary of claim tx (batch claim or claim limit)
        """
        w = wasm_limit_claimed
        order_id_list = w["order_id"].split(",")

        out = []
        for i in range(len(order_id_list)):
            # Get info for one executed order
            order_id = order_id_list[i]
            amount_claimed = w["amount_claimed"].split(",")[i]
            placed_quantity = w["placed_quantity"].split(",")[i]
            quantity_remaining = w["quantity_remaining"].split(",")[i]
            order_denom = w["order_denom"].split(",")[i]
            output_denom = w["output_denom"].split(",")[i]
            owner = w["owner"].split(",")[i]

            # Important filter since batch claims can have non-related wallets
            if owner != wallet_address:
                continue

            # Find (sent_amt, sent_cur) of placed limit order
            sent_amt_raw = int(placed_quantity) - int(quantity_remaining)
            sent_denom = order_denom
            sent_amt, sent_cur = denoms.amount_currency_from_raw(sent_amt_raw, sent_denom, OSMO_NODE)

            # Find (rec_amt, rec_cur)
            rec_amt_raw = amount_claimed
            rec_denom = output_denom
            rec_amt, rec_cur = denoms.amount_currency_from_raw(rec_amt_raw, rec_denom, OSMO_NODE)

            out.append((order_id, sent_amt, sent_cur, rec_amt, rec_cur))

        logging.info("limit order trades found: %s", out)
        return out


def handle(exporter, txinfo, msginfo):
    execute_contract_message = msginfo.execute_contract_message

    if "place_limit" in execute_contract_message:
        return _handle_place_limit(exporter, txinfo, msginfo)
    elif "cancel_limit" in execute_contract_message:
        return _handle_cancel_limit(exporter, txinfo, msginfo)
    elif "claim_limit" in execute_contract_message:
        return _handle_claim_limit(exporter, txinfo, msginfo)
    elif "batch_claim" in execute_contract_message:
        return _handle_batch_claim(exporter, txinfo, msginfo)

    raise Exception("Unable to handle tx in cosmwasmpool.handle()")


# opens limit order
def _handle_place_limit(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    contract = msginfo.contract
    events_by_type = msginfo.events_by_type

    if len(transfers_out) == 1 and len(transfers_in) == 0:
        sent_amt, sent_cur = transfers_out[0]

        # Find order info
        order_id = events_by_type["wasm"]["order_id"]

        # Find ask currency
        wasm = events_by_type["wasm"]
        ask_denom = wasm["output_denom"]
        _, ask_currency = denoms.amount_currency_from_raw(0, ask_denom, OSMO_NODE)

        # Create csv row
        row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)
        row.comment += f"[cosmwaspool place limit][sent {sent_amt} {sent_cur}][ask_currency={ask_currency}]" \
                       f"[order_id={order_id}, contract={contract}]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle to in cosmwasmpool._handle_place_limit()")


# cancels limit order
def _handle_cancel_limit(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    contract = msginfo.contract
    events_by_type = msginfo.events_by_type

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        rec_amt, rec_cur = transfers_in[0]

        # Find order info
        order_id = events_by_type["wasm"]["order_id"]

        # Create csv row
        row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)
        row.comment += f"[cosmwasmpool cancel limit][received {rec_amt} {rec_cur}]" \
                       f"[order_id={order_id}, contract={contract}]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle to in cosmwasmpool._handle_cancel_limit()")


# execute one limit order
def _handle_claim_limit(exporter, txinfo, msginfo):
    _handle_claim(exporter, txinfo, msginfo)


# execute multiple limit orders
def _handle_batch_claim(exporter, txinfo, msginfo):
    _handle_claim(exporter, txinfo, msginfo)


def _handle_claim(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net
    events_by_type = msginfo.events_by_type
    contract = msginfo.contract
    wallet_address = exporter.wallet_address

    if len(transfers_in) > 0 and len(transfers_out) == 0:
        # Find trade info in this list of limit orders executed
        wasm_limit_claimed = events_by_type["wasm-limitClaimed"]
        swaps = LimitOrders().claim(wasm_limit_claimed, wallet_address)

        # Create csv row(s)
        rows = []
        for order_id, sent_amt, sent_cur, rec_amt, rec_cur in swaps:
            row = make_osmo_swap_tx(txinfo, msginfo, sent_amt, sent_cur, rec_amt, rec_cur)
            row.comment += f"[cosmwasmpool claim]" \
                           f"[received {str(transfers_in).strip('[]')} (for this message)]" \
                           f"[order_id={order_id}, contract={contract}]"
            rows.append(row)

        util_osmo._ingest_rows(exporter, rows)
        return

    # raise Exception("Unable to handle tx in cosmwasmpool._handle_claim()")
