import logging
import requests
import time
from staketaxcsv.settings_csv import SOL_HELIUS_API_KEY
HELIUS_API_URL = "https://api.helius.xyz/"
LIMIT_MINT_ACCOUNTS = 100


class HeliusAPI:

    session = requests.Session()

    @classmethod
    def _fetch(cls, uri, params):
        if not SOL_HELIUS_API_KEY:
            logging.error("Unable to fetch helius api.  Missing SOL_HELIUS_API_KEY.  "
                          "Define STAKETAX_SOL_HELIUS_API_KEY environment variable.", )
            return None
        url = HELIUS_API_URL + uri + "?api-key=" + SOL_HELIUS_API_KEY

        logging.info("Fetching helius url %s with params %s ...", url, params)
        response = cls.session.post(url, json=params, headers={})

        data = response.json()
        time.sleep(0.1)

        return data

    # https://docs.helius.dev/solana-apis/token-metadata-api
    @classmethod
    def _get_token_metadata(cls, mints_list):
        uri = "v0/token-metadata"
        params = {
            "mintAccounts": mints_list,
            "includeOffChain": False,
            "disableCache": False,
        }

        data = cls._fetch(uri, params)
        return data

    @classmethod
    def get_token_symbols(cls, mint_addresses):
        data = cls._get_token_metadata(mint_addresses)

        out = []
        for elem in data:
            try:
                symbol = elem["onChainMetadata"]["metadata"]["data"]["symbol"]
            except (KeyError, TypeError) as e:
                symbol = None
            out.append(symbol)
        return out

    @classmethod
    def get_token_symbol(cls, mint_address):
        return cls.get_token_symbols([mint_address])[0]


def get_token_symbols_no_limit(mint_addresses):
    out = []
    for i in range(0, len(mint_addresses), LIMIT_MINT_ACCOUNTS):
        result = HeliusAPI.get_token_symbols(mint_addresses[i:i + LIMIT_MINT_ACCOUNTS])
        out.extend(result)
    return out
