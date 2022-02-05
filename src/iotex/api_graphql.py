import logging
import requests

# Basic documentation and playground available here
IOTEX_GRAPHQL_URL = "https://iotexscan.io/api-gateway"
IOTEX_GRAPHQL_LIMIT = 100


class IoTexGraphQL:

    @classmethod
    def account_exists(cls, address):
        return bool(cls.num_actions(address))

    @classmethod
    def num_actions(cls, address):
        payload = {
            "operationName": "NumActions",
            "query": ("query NumActions($address: String!) { "
                        "getAccount(address:$address) { accountMeta { numActions } } }"),
            "variables": {"address": address}
        }

        data, status_code = cls._query(IOTEX_GRAPHQL_URL, payload)

        if status_code != 200:
            return False

        return data.get("data", {}).get("getAccount", {}).get("accountMeta", {}).get("numActions", 0)

    @classmethod
    def get_actions(cls, address, start, count):
        query = ("query GetActions($address:String!, $start:BigNumber!, $count:BigNumber!) { "
                    "getActions(byAddr:{ address:$address, start: $start, count: $count }) { "
                        "actionInfo { "
                            "actHash "
                            "timestamp { seconds } "
                            "action { "
                                "senderPubKey "
                                "core { "
                                    "gasLimit "
                                    "gasPrice "
                                    "transfer { amount recipient }"
                                "} "
                            "} "
                        "} "
                    "} "
                 "}")
        payload = {
            "operationName": "GetActions",
            "query": query,
            "variables": {"address": address, "start": start, "count": count}
        }

        data, status_code = cls._query(IOTEX_GRAPHQL_URL, payload)

        if status_code != 200:
            return False

        return data.get("data", {}).get("getActions", {}).get("actionInfo", [])

    @classmethod
    def get_action(cls, txhash):
        query = ("query GetAction($hash:String!) { "
                    "getActions(byHash:{ actionHash:$hash, checkingPending:true }) { "
                        "actionInfo { "
                            "actHash "
                            "timestamp { seconds } "
                            "action { "
                                "senderPubKey "
                                "core { "
                                    "gasLimit "
                                    "gasPrice "
                                    "transfer { amount recipient }"
                                "} "
                            "} "
                        "} "
                    "} "
                 "}")
        payload = {
            "operationName": "GetAction",
            "query": query,
            "variables": {"hash": txhash}
        }

        data, status_code = cls._query(IOTEX_GRAPHQL_URL, payload)

        if status_code != 200:
            return False

        return data.get("data", {}).get("getActions", {}).get("actionInfo", [])

    @classmethod
    def _query(cls, url, payload):
        logging.info("Querying IOTEX GRAPHQL url=%s...", url)
        response = requests.post(url, json=payload, headers={})
        return response.json(), response.status_code
