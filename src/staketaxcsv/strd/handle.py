from staketaxcsv.common.ibc.util_ibc import aggregate_transfers
from staketaxcsv.common.ibc import make_tx


def handle_claim_free_amount(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) > 0 and len(transfers_out) == 0:
        for amount, currency in aggregate_transfers(transfers_in):
            row = make_tx.make_airdrop_tx(txinfo, msginfo, amount, currency)
            exporter.ingest_row(row)
        return

    raise Exception("Unable to handle message in handle_claim_free_amount()")


def handle_liquid_stake(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        received_amount, received_currency = transfers_in[0]
        sent_amount, sent_currency = transfers_out[0]

        row = make_tx.make_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle message in handle_liquid_stake()")
