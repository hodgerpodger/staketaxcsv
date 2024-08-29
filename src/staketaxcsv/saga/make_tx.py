from staketaxcsv.common.Exporter import Row
from staketaxcsv.common.ExporterTypes import TX_TYPE_AIRDROP
from staketaxcsv.saga import constants as co


def make_genesis_airdrop_tx(amount_saga, wallet_address):
    row = Row(
        timestamp="2024-04-08 00:00:00",  # timestamp of height 1 (https://www.mintscan.io/saga/block/1)
        tx_type=TX_TYPE_AIRDROP,
        received_amount=amount_saga,
        received_currency=co.CURRENCY_SAGA,
        sent_amount="",
        sent_currency="",
        fee="",
        fee_currency="",
        exchange=co.EXCHANGE_SAGA,
        wallet_address=wallet_address,
        txid="saga_genesis_airdrop",
        url=""
    )
    return row
