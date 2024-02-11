from staketaxcsv.common.Exporter import Row
from staketaxcsv.common.ExporterTypes import TX_TYPE_AIRDROP
from staketaxcsv.dym import constants as co


def make_genesis_airdrop_tx(amount_dym, wallet_address):
    row = Row(
        timestamp="2024-02-06 11:00:00",  # timestamp of height 1 (https://www.mintscan.io/dymension/block/1)
        tx_type=TX_TYPE_AIRDROP,
        received_amount=amount_dym,
        received_currency=co.CURRENCY_DYM,
        sent_amount="",
        sent_currency="",
        fee="",
        fee_currency="",
        exchange=co.EXCHANGE_DYM,
        wallet_address=wallet_address,
        txid="dymension_genesis_airdrop",
        url=""
    )
    return row
