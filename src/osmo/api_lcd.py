

import logging
import requests
import time
from settings_csv import OSMO_LCD_NODE


class LcdAPI:

    @classmethod
    def get_reward_address(cls, wallet_address):
        uri = "/cosmos/distribution/v1beta1/delegators/{}/withdraw_address".format(wallet_address)
        data = cls._query(uri)

        result = data.get("withdraw_address", None)
        return result


    @classmethod
    def _query(cls, uri):
        url = "{}{}".format(OSMO_LCD_NODE, uri)
        logging.info("Querying url=%s...", url)
        response = requests.get(url)
        data = response.json()
        time.sleep(1)
        return data
