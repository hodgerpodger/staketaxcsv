import json
import logging
import os
import requests

from staketaxcsv.dym.make_tx import make_genesis_airdrop_tx
from staketaxcsv.dym.constants import EXP18

GENESIS_JSON = os.environ.get("STAKETAX_DYM_GENESIS_JSON", os.path.join(os.path.dirname(__file__), "genesis.json"))
GENESIS_URL = "https://github.com/dymensionxyz/networks/raw/main/mainnet/dymension/genesis.json"


def genesis_airdrop(wallet_address, exporter):
    amount_dym = _genesis_airdrop_dym_amount(wallet_address)
    if amount_dym:
        row = make_genesis_airdrop_tx(amount_dym, wallet_address)
        exporter.ingest_row(row)


def _genesis_airdrop_dym_amount(wallet_address):
    data = _get_genesis_data()

    balances = data["app_state"]["bank"]["balances"]
    for balance in balances:
        if balance["address"] == wallet_address:
            amount = balance["coins"][0]["amount"]
            return float(amount) / EXP18

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
