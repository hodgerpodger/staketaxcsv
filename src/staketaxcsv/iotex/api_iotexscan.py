import logging

import requests

# No documentation available for this,
# just inspect requests on chrome/devtools/network.
IOTEX_SCAN_URL = "https://iotexscan.io"


class IoTexScan:

    @classmethod
    def num_stake_actions(cls, address):
        url = f"{IOTEX_SCAN_URL}/api/services/action/queries/getNumStakeActionsByAddress"
        payload = {
            "params": {
                "address": address,
                "from": ""
            },
            "meta": {}
        }

        data, status_code = cls._query(url, payload)

        if status_code != 200:
            return False

        return int(data.get("result", 0))

    @classmethod
    def get_stake_actions(cls, address, page, limit):
        url = f"{IOTEX_SCAN_URL}/api/services/action/queries/getStakeActionsByAddress"
        payload = {
            "params": {
                "address": address,
                "page": page,
                "limit": limit,
                "from": ""
            },
            "meta": {}
        }

        data, status_code = cls._query(url, payload)

        if status_code != 200:
            return False

        return data.get("result", [])

    @classmethod
    def _query(cls, url, payload):
        logging.info("Querying iotex scan url=%s...", url)
        response = requests.post(url, json=payload, headers={})
        return response.json(), response.status_code
