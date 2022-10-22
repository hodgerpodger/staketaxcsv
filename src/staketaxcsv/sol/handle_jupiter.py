from staketaxcsv.common.make_tx import make_swap_tx
from staketaxcsv.sol.constants import CURRENCY_SOL
from staketaxcsv.sol.handle_simple import handle_unknown_detect_transfers


def handle_jupiter_aggregator_v2(exporter, txinfo):
    txinfo.comment = "jupiter_aggregator"
    _handle_jupiter_aggregator(exporter, txinfo)


def handle_jupiter_aggregator_v3(exporter, txinfo):
    txinfo.comment = "jupiter_aggregator_v3"
    _handle_jupiter_aggregator(exporter, txinfo)


def handle_jupiter_aggregator_v4(exporter, txinfo):
    txinfo.comment = "jupiter_aggregator_v4"
    _handle_jupiter_aggregator(exporter, txinfo)


def _handle_jupiter_aggregator(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers_net

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        sent_amount, sent_currency, _, _ = transfers_out[0]
        received_amount, received_currency, _, _ = transfers_in[0]

        # For SOL transfers, adjust fee from zero to non-zero if applicable
        if sent_currency == CURRENCY_SOL and txinfo.fee == "" and txinfo.fee_blockchain > 0:
            txinfo.fee = txinfo.fee_blockchain
            sent_amount -= txinfo.fee_blockchain
        if received_currency == CURRENCY_SOL and txinfo.fee == "" and txinfo.fee_blockchain > 0:
            txinfo.fee = txinfo.fee_blockchain

        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    else:
        handle_unknown_detect_transfers(exporter, txinfo)
