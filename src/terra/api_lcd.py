"""
LCD documentation:
 * https://lcd.terra.dev/swagger/#/
 * https://github.com/terra-money/terra.py/tree/main/terra_sdk/client/lcd/api
"""

import logging
import time

import requests
from settings_csv import TERRA_LCD_NODE


class LcdAPI:

    @classmethod
    def contract_info(cls, contract):
        url = "{}/wasm/contracts/{}".format(TERRA_LCD_NODE, contract)

        logging.info("Querying lcd for contract=%s...", contract)
        response = requests.get(url)
        data = response.json()
        time.sleep(0.1)

        return data
