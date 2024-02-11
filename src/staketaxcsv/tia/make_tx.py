from staketaxcsv.common.Exporter import Row
from staketaxcsv.common.ExporterTypes import TX_TYPE_AIRDROP
from staketaxcsv.tia import constants as co


def make_genesis_airdrop_tx(amount_tia, wallet_address):
    row = Row(
        timestamp="2023-10-31 14:00:00",  # timestamp of height 1 (https://www.mintscan.io/celestia/block/1)
        tx_type=TX_TYPE_AIRDROP,
        received_amount=amount_tia,
        received_currency=co.CURRENCY_TIA,
        sent_amount="",
        sent_currency="",
        fee="",
        fee_currency="",
        exchange=co.EXCHANGE_CELESTIA,
        wallet_address=wallet_address,
        txid="celestia_genesis_airdrop",
        url=""
    )
    return row
