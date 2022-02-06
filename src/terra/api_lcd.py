"""
LCD documentation:
 * https://lcd.terra.dev/swagger/#/
 * https://github.com/terra-money/terra.py/tree/main/terra_sdk/client/lcd/api
"""

import logging
import time
from urllib.parse import urlencode

import requests
from settings_csv import TERRA_LCD_NODE


def _query(uri_path, query_params, sleep_seconds=1):
    url = f"{TERRA_LCD_NODE}{uri_path}"
    logging.info("Requesting url %s?%s", url, urlencode(query_params))
    response = requests.get(url, query_params)

    time.sleep(sleep_seconds)
    return response.json()


class LcdAPI:

    @classmethod
    def contract_info(cls, contract):
        uri = "/wasm/contracts/{}".format(contract)
        logging.info("Querying lcd for contract=%s...", contract)
        data = _query(uri, {})
        return data
