from collections import defaultdict
import logging

from staketaxcsv.osmo.handle_claim import handle_claim
from staketaxcsv.osmo.handle_unknown import handle_unknown_detect_transfers
from staketaxcsv.osmo.make_tx import make_osmo_swap_tx
from staketaxcsv.common.ibc import util_ibc
TINY_AMOUNT = .0000000000001


def handle_swap(exporter, txinfo, msginfo):
    # Preprocessing step to parse staking reward events first, if exists.
    handle_claim(exporter, txinfo, msginfo)

    transfers_in, transfers_out = msginfo.transfers
    net_in, net_out = util_ibc.aggregate_transfers_net(transfers_in, transfers_out)

    logging.info("handle_swap(): net_in=%s, net_out=%s", net_in, net_out)

    if len(net_in) == 1 and len(net_out) == 1:
        sent_amount, sent_currency = net_out[0]
        received_amount, received_currency = net_in[0]

        row = make_osmo_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)
