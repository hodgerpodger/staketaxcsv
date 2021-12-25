
import logging
import requests
import time
import urllib.parse
from settings_csv import OSMO_HISTORICAL_NODE


class OsmoHistoricalAPI:

    @classmethod
    def get_symbol(cls, ibc_address):
        uri = "/search/v1/symbol?denom={}".format(urllib.parse.quote(ibc_address))
        data = cls._query(uri)
        if "symbol" in data:
            return data["symbol"]
        else:
            return None

    @classmethod
    def _query(cls, uri):
        url = "{}{}".format(OSMO_HISTORICAL_NODE, uri)
        logging.info("Querying url=%s...", url)
        response = requests.get(url)
        data = response.json()
        time.sleep(1)
        return data
