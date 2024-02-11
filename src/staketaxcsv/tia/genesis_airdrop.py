import json
import logging
import os
import requests

import staketaxcsv.tia.constants as co
from staketaxcsv.tia.make_tx import make_genesis_airdrop_tx

GENESIS_JSON = os.environ.get("STAKETAX_TIA_GENESIS_JSON", os.path.join(os.path.dirname(__file__), "genesis.json"))
GENESIS_URL = "https://raw.githubusercontent.com/celestiaorg/networks/master/celestia/genesis.json"


def genesis_airdrop(wallet_address, exporter):
    amount_tia = _genesis_airdrop_celestia_amount(wallet_address)
    if amount_tia:
        row = make_genesis_airdrop_tx(amount_tia, wallet_address)
        exporter.ingest_row(row)


def _genesis_airdrop_celestia_amount(wallet_address):
    data = _get_genesis_data()

    balances = data["app_state"]["bank"]["balances"]
    for balance in balances:
        if balance["address"] == wallet_address:
            amount = balance["coins"][0]["amount"]
            return float(amount) / co.MILLION

    return 0


def _get_genesis_data():
    if not os.path.exists(GENESIS_JSON):
        logging.info("Fetching genesis url %s ...", GENESIS_URL)
        response = requests.get(GENESIS_URL)
        with open(GENESIS_JSON, 'w') as file:
            file.write(response.text)

    with open(GENESIS_JSON, 'r') as file:
        data = json.load(file)
        return data
