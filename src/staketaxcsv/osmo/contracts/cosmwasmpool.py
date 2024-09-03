import logging
from staketaxcsv.common.make_tx import make_spend_fee_tx


class LimitOrders:
    # (contract, order_id) -> {
    #   <currency> -> <amount>
    # }
    orders = {}

    def place(self, contract, order_id, sent_amt, sent_cur):
        order_key = (contract, order_id)

        if order_key not in self.orders:
            self.orders[order_key] = {}
        if sent_cur not in self.orders[order_key]:
            self.orders[order_key][sent_cur] = 0
        self.orders[order_key][sent_cur] += sent_amt

        logging.info("LimitOrders.place(), order_key=%s, sent_amt=%s, sent_cur=%s", order_key, sent_amt, sent_cur)
        logging.info("LimitOrders.orders is now: %s", self.orders)

    def cancel(self, contract, order_id):
        order_key = (contract, order_id)

        if order_key in self.orders:
            del self.orders[order_key]

        logging.info("LimitOrders.cancel(), order_key=%s", order_key)
        logging.info("LimitOrders.orders is now: %s", self.orders)

    # this is like "executing" limit order
    def claim(self):
        pass


def handle(exporter, txinfo, msginfo):
    execute_contract_message = msginfo.execute_contract_message

    if "place_limit" in execute_contract_message:
        return _handle_place_limit(exporter, txinfo, msginfo)
    elif "cancel_limit" in execute_contract_message:
        return _handle_cancel_limit(exporter, txinfo, msginfo)
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
        order_id = events_by_type["wasm"]["order_id"]
        LimitOrders().place(contract, order_id, sent_amt, sent_cur)

        row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)
        row.comment += f"[cosmwaspool place limit][sent {sent_amt} {sent_cur}][order_id={order_id}, contract={contract}]"
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

        order_id = events_by_type["wasm"]["order_id"]
        LimitOrders().cancel(contract, order_id)

        row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)
        row.comment += f"[cosmwasmpool cancel limit][received {rec_amt} {rec_cur}][order_id={order_id}, contract={contract}]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle to in cosmwasmpool._handle_cancel_limit()")


# executes limit order(s)
def _handle_batch_claim(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    raise Exception("Unable to handle to in cosmwasmpool._handle_batch_claim()")
