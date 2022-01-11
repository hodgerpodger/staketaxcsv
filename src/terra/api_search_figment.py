import time

import requests
from settings_csv import TERRA_FIGMENT_KEY

# https://docs.figment.io/network-documentation/terra/enriched-apis/transaction-search
FIGMENT_SEARCH_URL = "https://terra--search.datahub.figment.io/apikey/{}/transactions_search".format(TERRA_FIGMENT_KEY)
LIMIT_FIGMENT = 1000


class SearchAPIFigment:

    @classmethod
    def get_txs(cls, address, offset=None, limit=None):
        url = "{}".format(FIGMENT_SEARCH_URL)
        limit_arg = limit if limit else LIMIT_FIGMENT

        data = {
            "network": "terra",
            "account": [address],
            "chain_ids": ["columbus-3", "columbus-4", "columbus-5"],
            "limit": limit_arg
        }
        if offset:
            data["offset"] = offset

        response = requests.post(url, json=data)
        response_data = response.json()

        time.sleep(0.2)
        return response_data
