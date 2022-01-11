
import logging
import time

import requests

FCD_URL = "https://fcd.terra.dev"
LIMIT_FCD = 100


class FcdAPI:

    @classmethod
    def get_tx(cls, txhash):
        url = "{}/v1/tx/{}".format(FCD_URL, txhash)
        data = cls._query(url)

        cls._add_events_by_type(data)
        return data

    @classmethod
    def get_txs(cls, address, offset=None):
        url = "{}/v1/txs?account={}&limit={}".format(FCD_URL, address, LIMIT_FCD)
        if offset:
            url += "&offset={}".format(offset)
        data = cls._query(url)

        for elem in data["txs"]:
            cls._add_events_by_type(elem)
        return data

    @classmethod
    def _query(cls, url):
        logging.info("Querying FCD url=%s...", url)
        response = requests.get(url)
        data = response.json()
        time.sleep(5)
        return data

    @classmethod
    def _add_events_by_type(cls, elem):
        if "logs" in elem:
            logs = elem["logs"]
            for log in logs:
                if "events" in log and "events_by_type" not in log:
                    events = log["events"]
                    log["events_by_type"] = cls._events_by_type(events)

    @classmethod
    def _events_by_type(cls, events):
        out = {}

        for event in events:
            attributes = event["attributes"]
            type = event["type"]
            info = {}

            for kv in attributes:
                k, v = kv.get("key", None), kv.get("value", None)
                if k not in info:
                    info[k] = []
                info[k].append(v)

            out[type] = info

        return out
