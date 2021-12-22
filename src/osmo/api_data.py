
import logging
import requests
import time

from settings_csv import OSMO_DATA_NODE
LIMIT = 50


class OsmoDataAPI:

    @classmethod
    def get_count_txs(cls, address):
        uri = "/txs/v1/tx/count/{}".format(address)
        data = cls._query(uri)

        count = 0
        for row in data:
            count += row["count"]
        return count

    @classmethod
    def get_txs(cls, address, offset=None):
        uri = "/txs/v1/tx/address/{}?limit={}".format(address, LIMIT)
        if offset:
            uri += "&offset={}".format(offset)
        data = cls._query(uri)

        # Extract "tx_response" (found to be common data across multiple APIs)
        result = [x["tx_response"] for x in data]
        return result

    @classmethod
    def _query(cls, uri):
        url = "{}{}".format(OSMO_DATA_NODE, uri)
        logging.info("Querying url=%s...", url)
        response = requests.get(url)
        data = response.json()
        time.sleep(1)
        return data
