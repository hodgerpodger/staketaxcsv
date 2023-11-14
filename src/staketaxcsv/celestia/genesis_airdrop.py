import requests
import json
import staketaxcsv.common.ibc.api_lcd_v2
import staketaxcsv.celestia.constants as co
from staketaxcsv.celestia.make_tx import make_genesis_airdrop_tx
from staketaxcsv.settings_csv import CELESTIA_NODE


def genesis_airdrop(wallet_address, exporter):
    amount_tia = _genesis_airdrop_celestia_amount(wallet_address)
    if amount_tia:
        row = make_genesis_airdrop_tx(amount_tia, wallet_address)
        exporter.ingest_row(row)


def _genesis_airdrop_celestia_amount(wallet_address):
    response = requests.get(co.GENESIS_URL)
    data = json.loads(response.text)
    balances = data["app_state"]["bank"]["balances"]
    for balance in balances:
        if balance["address"] == wallet_address:
            amount = balance["coins"][0]["amount"]
            return float(amount) / co.MILLION

    return 0
