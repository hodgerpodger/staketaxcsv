import json
import logging
import os

# From https://github.com/solana-labs/token-list/blob/main/src/tokens/solana.tokenlist.json
# https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json
PATH_JSON = os.path.dirname(os.path.realpath(__file__)) + "/solana.tokenlist.json"


class Tickers:
    loaded = False
    tickers = {}

    @classmethod
    def _load(cls):
        if cls.loaded is False:
            logging.info("Loading {}".format(PATH_JSON))
            with open(PATH_JSON) as f:
                data = json.load(f)
                for info in data["tokens"]:
                    address = info["address"]
                    symbol = info["symbol"]

                    # extra stuff I can probably use later
                    # name = info["name"]
                    # logouri = info.get("logoURI")

                    cls.tickers[address] = symbol
            cls.loaded = True

    @classmethod
    def get(cls, address):
        cls._load()

        ticker = cls.tickers.get(address, None)
        if ticker:
            return ticker
        else:
            return address
