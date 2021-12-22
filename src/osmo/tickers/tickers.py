
"""
usage: python3 osmo/tickers/tickers.py
  * Refreshes osmo/tickers/tickers.json

"""

import json
import pprint
import os
import requests
URL = "https://raw.githubusercontent.com/osmosis-labs/osmosis/main/app/whitelist_feetokens.go"
TICKERS_JSON = os.path.dirname(os.path.realpath(__file__)) + "/tickers.json"


class TickersIBC:

    tickers = {}

    @classmethod
    def write_json(cls):
        r = requests.get(URL)
        text = r.text

        # Download url with <ibc_address> -> <symbol> data.
        tickers = {}
        for line in text.splitlines():
            if ",ibc/" in line:
                symbol, ibc_address, _ = line.split(",")
                tickers[ibc_address] = symbol.upper()

        # Write to ticker.json
        with open(TICKERS_JSON, "w") as f:
            json.dump(tickers, f, indent=4)
        print("Wrote to {}".format(TICKERS_JSON))

    @classmethod
    def lookup(cls, ibc_address):
        if not cls.tickers:
            with open(TICKERS_JSON, "r") as f:
                cls.tickers = json.load(f)

        return cls.tickers.get(ibc_address, "")


if __name__ == "__main__":
    TickersIBC.write_json()

