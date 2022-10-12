"""
LCD documentation:
 * https://lcd.terra.dev/swagger/#/
 * https://github.com/terra-money/terra.py/tree/main/terra_sdk/client/lcd/api
"""

import logging
import time
from urllib.parse import urlencode

import requests
from staketaxcsv.common.ibc.api_common import EVENTS_TYPE_RECIPIENT, EVENTS_TYPE_SENDER, EVENTS_TYPE_SIGNER
from staketaxcsv.settings_csv import TERRA_LCD_NODE

LIMIT_TX_QUERY = 50


class LcdAPI:
    session = requests.Session()

    @classmethod
    def contract_info(cls, contract):
        uri = "/wasm/contracts/{}".format(contract)
        logging.info("Querying lcd for contract = %s ...", contract)
        data = cls._query(uri, {})
        return data

    @classmethod
    def _query(cls, uri_path, query_params, sleep_seconds=1):
        url = f"{TERRA_LCD_NODE}{uri_path}"
        logging.info("Requesting url %s?%s", url, urlencode(query_params))
        response = cls.session.get(url, params=query_params)

        time.sleep(sleep_seconds)
        return response.json()

    @classmethod
    def _get_txs(cls, wallet_address, events_type, offset, limit, sleep_seconds):
        uri_path = "/cosmos/tx/v1beta1/txs"
        query_params = {
            "order_by": "ORDER_BY_DESC",
            "pagination.limit": limit,
            "pagination.offset": offset,
            "pagination.count_total": True,
        }
        if events_type == EVENTS_TYPE_SENDER:
            query_params["events"] = f"message.sender='{wallet_address}'"
        elif events_type == EVENTS_TYPE_RECIPIENT:
            query_params["events"] = f"transfer.recipient='{wallet_address}'"
        elif events_type == EVENTS_TYPE_SIGNER:
            query_params["events"] = f"message.signer='{wallet_address}'"
        else:
            raise Exception("Add case for events_type: {}".format(events_type))

        data = cls._query(uri_path, query_params, sleep_seconds)

        return data

    @classmethod
    def num_txs(cls, wallet_address):
        data = cls._get_txs(wallet_address, EVENTS_TYPE_SENDER, 0, LIMIT_TX_QUERY, 0)
        num_send = int(data["pagination"]["total"])

        data = cls._get_txs(wallet_address, EVENTS_TYPE_RECIPIENT, 0, LIMIT_TX_QUERY, 0)
        num_receiver = int(data["pagination"]["total"])

        return num_send + num_receiver

    @classmethod
    def _accounts(cls, wallet_address):
        uri_path = "/cosmos/auth/v1beta1/accounts/{}".format(wallet_address)
        data = cls._query(uri_path, {})

        return data

    @classmethod
    def has_txs(self, wallet_address):
        data = self._accounts(wallet_address)
        if "account" in data:
            return True
        else:
            return False
