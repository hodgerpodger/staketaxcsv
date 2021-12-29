
import logging
import requests
import time
OSMO_TX_NODE = "https://api-osmosis.cosmostation.io"


class OsmoTxAPI:

    @classmethod
    def get_tx(cls, txid):
        uri = "/v1/tx/hash/{}".format(txid)
        data = cls._query(uri)

        result = data["data"]
        return result

    @classmethod
    def _query(cls, uri):
        url = "{}{}".format(OSMO_TX_NODE, uri)
        logging.info("Querying url=%s...", url)
        response = requests.get(url)
        data = response.json()
        time.sleep(1)
        return data
