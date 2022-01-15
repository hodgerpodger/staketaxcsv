from common.ErrorCounter import ErrorCounter
from common.make_tx import make_unknown_tx
from terra import util_terra
from terra.constants import CUR_BLUNA, CUR_LUNA
from terra.make_tx import make_swap_tx_terra, make_unbond_tx


def handle_bond(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Get sent amount
    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid)
    sent_amount, sent_currency = transfers_out[0]

    try:
        # Get minted amount of bluna
        received_currency = CUR_BLUNA
        received_amount_string = elem["logs"][0]["events_by_type"]["from_contract"]["minted"][0]
        received_amount = util_terra._float_amount(received_amount_string, CUR_BLUNA)

        row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    except Exception:
        row = make_unknown_tx(txinfo)
        exporter.ingest_row(row)
        ErrorCounter.increment("handle_bond_unknown", txid)


def handle_unbond(exporter, elem, txinfo):
    row = make_unbond_tx(txinfo)
    exporter.ingest_row(row)


def handle_unbond_withdraw(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Get received amount
    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid)
    received_amount, received_currency = transfers_in[0]

    sent_amount = received_amount
    sent_currency = CUR_BLUNA
    assert(received_currency == CUR_LUNA)

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    exporter.ingest_row(row)
