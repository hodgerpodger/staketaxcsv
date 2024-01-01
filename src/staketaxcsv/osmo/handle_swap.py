from collections import defaultdict

from staketaxcsv.osmo.handle_claim import handle_claim
from staketaxcsv.osmo.handle_unknown import handle_unknown_detect_transfers
from staketaxcsv.osmo.make_tx import make_osmo_swap_tx


def handle_swap(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    # Preprocessing step to parse staking reward events first, if exists.
    handle_claim(exporter, txinfo, msginfo)

    # Remove intermediate swap tokens (A -> B -> C; remove B)
    transfers_common = set(transfers_in).intersection(set(transfers_out))
    for t in transfers_common:
        transfers_in.remove(t)
        transfers_out.remove(t)

    # Sum up by token
    transfers_in, transfers_out = _aggregate_transfers(transfers_in, transfers_out)

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
    aggregated_transfers_in = defaultdict(float)
    for amount, currency in transfers_in:
        aggregated_transfers_in[currency] += amount

    aggregated_transfers_out = defaultdict(float)
    for amount, currency in transfers_out:
        aggregated_transfers_out[currency] += amount

    # Correctly format the aggregated results as (amount, currency)
    result_transfers_in = [(amt, cur) for cur, amt in aggregated_transfers_in.items()]
    result_transfers_out = [(amt, cur) for cur, amt in aggregated_transfers_out.items()]

    return result_transfers_in, result_transfers_out
