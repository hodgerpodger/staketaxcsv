# Unknown program DjVE6JNiYqPL2QXyCUUh8rNjHrbz9hXHNYt99MQ59qw1

from common.make_tx import make_swap_tx
from sol.handle_simple import handle_unknown


def handle_2kd(exporter, txinfo):
    _handle_as_swap(exporter, txinfo)


def handle_djv(exporter, txinfo):
    _handle_as_swap(exporter, txinfo)


def _handle_as_swap(exporter, txinfo):
    log_instructions = txinfo.log_instructions
    transfers_in, transfers_out, transfers_unknown = txinfo.transfers

    if ("Swap" in log_instructions
       and len(transfers_in) == 1
       and len(transfers_out) == 1):

        sent_amount, sent_currency, _, _ = transfers_out[0]
        received_amount, received_currency, _, _ = transfers_in[0]

        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    else:
        handle_unknown(exporter, txinfo)
