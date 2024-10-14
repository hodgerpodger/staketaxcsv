from staketaxcsv.osmo.make_tx import make_osmo_swap_tx, make_osmo_tx
from staketaxcsv.common.ExporterTypes import TX_TYPE_TFM_SUBMIT_LIMIT_ORDER, TX_TYPE_TFM_CANCEL_LIMIT_ORDER


class LimitOrder:

    orders = {}

    def submit(self, msginfo):
        transfers_in, transfers_out = msginfo.transfers
        assert len(transfers_in) == 0
        assert len(transfers_out) == 1
        sent_amount, sent_currency = transfers_out[0]

        order_id = msginfo.events_by_type["wasm"]["order_id"]
        self.orders[order_id] = (sent_amount, sent_currency)

        comment_text = f"[tfm limit order, submit, order_id={order_id}, sent {sent_amount} {sent_currency}]"
        return comment_text

    def execute(self, msginfo):
        transfers_in, transfers_out = msginfo.transfers
        assert len(transfers_in) == 1
        assert len(transfers_out) == 0
        receive_amount, receive_currency = transfers_in[0]

        order_id = msginfo.events_by_type["wasm"]["order_id"]
        sent_amount, sent_currency = self.orders[order_id]

        comment_text = f"[tfm limit order, execute, order_id={order_id}, received {receive_amount} {receive_currency}"
        return sent_amount, sent_currency, receive_amount, receive_currency, comment_text

    def cancel(self, msginfo):
        transfers_in, transfers_out = msginfo.transfers
        assert len(transfers_in) == 1
        assert len(transfers_out) == 0
        receive_amount, receive_currency = transfers_in[0]

        order_id = msginfo.events_by_type["wasm"]["order_id"]
        comment_text = f"[tfm limit order, cancel, order_id={order_id}, received back {receive_amount} {receive_currency}]"

        return comment_text


def handle_execute_swap_operations(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        received_amount, received_currency = transfers_in[0]
        sent_amount, sent_currency = transfers_out[0]

        row = make_osmo_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in tfm.handle_execute_swap_operations()")


def handle_limit_order(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    execute_contract_message = msginfo.execute_contract_message

    if len(transfers_in) == 0 and len(transfers_out) == 1 and "submit_order" in execute_contract_message:
        return _handle_submit_order(exporter, txinfo, msginfo)
    elif len(transfers_in) == 1 and len(transfers_out) == 0 and "execute_order" in execute_contract_message:
        return _handle_execute_order(exporter, txinfo, msginfo)
    elif len(transfers_in) == 1 and len(transfers_out) == 0 and "cancel_order" in execute_contract_message:
        return _handle_cancel_order(exporter, txinfo, msginfo)

    raise Exception("Unable to handle tx in tfm.handle_limit_order()")


def _handle_submit_order(exporter, txinfo, msginfo):
    comment_text = LimitOrder().submit(msginfo)

    row = make_osmo_tx(txinfo, msginfo, "", "", "", "", tx_type=TX_TYPE_TFM_SUBMIT_LIMIT_ORDER)
    row.comment += comment_text
    exporter.ingest_row(row)


def _handle_execute_order(exporter, txinfo, msginfo):
    sent_amount, sent_cur, rec_amount, rec_cur, comment_text = LimitOrder().execute(msginfo)

    row = make_osmo_swap_tx(txinfo, msginfo, sent_amount, sent_cur, rec_amount, rec_cur)
    row.comment += comment_text
    exporter.ingest_row(row)


def _handle_cancel_order(exporter, txinfo, msginfo):
    comment_text = LimitOrder().cancel(msginfo)

    row = make_osmo_tx(txinfo, msginfo, "", "", "", "", tx_type=TX_TYPE_TFM_CANCEL_LIMIT_ORDER)
    row.comment += comment_text
    exporter.ingest_row(row)
