from unittest.mock import patch
import json
import os
from functools import wraps

from tests.settings_test import DATADIR
from tests.mock_lcd import MockLcdAPI_v1, MockLcdAPI_v2, MockCosmWasmLcdAPI
from tests.mock_osmo import mock_get_symbol, mock_get_exponent
from tests.mock_mintscan import MockMintscanAPI
TESTDATADIR = DATADIR + "/load_tx"


def load_tx(wallet_address, txid, get_tx_func):
    json_path = f"{TESTDATADIR}/load_tx-{wallet_address}-{txid}.json"
    if not os.path.exists(json_path):
        elem = get_tx_func(txid)
        with open(json_path, "w") as f:
            json.dump(elem, f, indent=4)

    with open(json_path, "r") as f:
        elem = json.load(f)

    return elem


def apply_ibc_patches(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        with patch("staketaxcsv.settings_csv.DB_CACHE", False), \
             patch("staketaxcsv.common.ibc.denoms.LcdAPI_v1", new=MockLcdAPI_v1), \
             patch("staketaxcsv.common.ibc.api_lcd_v1.LcdAPI_v1", new=MockLcdAPI_v1), \
             patch("staketaxcsv.common.ibc.api_lcd_v2.LcdAPI_v2", new=MockLcdAPI_v2), \
             patch("staketaxcsv.common.ibc.api_mintscan_v1.MintscanAPI", new=MockMintscanAPI), \
             patch("staketaxcsv.common.ibc.tx_data.MintscanAPI", new=MockMintscanAPI), \
             patch("staketaxcsv.common.ibc.api_lcd_cosmwasm.CosmWasmLcdAPI", new=MockCosmWasmLcdAPI), \
             patch("staketaxcsv.osmo.denoms._symbol", mock_get_symbol), \
             patch("staketaxcsv.osmo.denoms._exponent", mock_get_exponent):
            return func(*args, **kwargs)

    return wrapper
