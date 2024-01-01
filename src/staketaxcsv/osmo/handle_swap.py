from collections import defaultdict

from staketaxcsv.osmo.handle_claim import handle_claim
from staketaxcsv.osmo.handle_unknown import handle_unknown_detect_transfers
from staketaxcsv.osmo.make_tx import make_osmo_swap_tx


def handle_swap(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net

    # Preprocessing step to parse staking reward events first, if exists.
    handle_claim(exporter, txinfo, msginfo)

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        sent_amount, sent_currency = transfers_out[0]
        received_amount, received_currency = transfers_in[0]

        row = make_osmo_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def _aggregate_transfers(transfers_in, transfers_out):
    # 	Example:
    # 	[(0.000528, 'TIA'), (0.001072, 'TIA'), (1.595204, 'TIA'), (0.003196, 'TIA')]
    #   -> [(1.6, 'TIA')]

    # Sum net amounts for each currency
    net = defaultdict(float)
    for amount, currency in transfers_in:
        net[currency] += amount
    for amount, currency in transfers_out:
        net[currency] -= amount

    # Convert to transfers_in, transfers_out lists
    net_in, net_out = [], []
    for cur, amt in net.items():
        # Skip for neglible amounts
        if -TINY_AMOUNT <= amt <= TINY_AMOUNT:
            continue

        if amt > 0:
            net_in.append((amt, cur))
        else:
            net_out.append((-amt, cur))

    return net_in, net_out
