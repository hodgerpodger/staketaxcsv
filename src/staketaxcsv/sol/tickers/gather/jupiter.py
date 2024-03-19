"""
usage: python3 staketaxcsv/sol/tickers/gather/jupiter.py

* Writes tickers json file to staketaxcsv/sol/tickers/token_lists/jupiter.YYYYMMDD.json,
  which effectively updates the recognized token symbols for the solana report.

"""
import logging

import requests
import json
import os
from datetime import datetime

from staketaxcsv.sol.tickers.tickers import TOKEN_LISTS_DIR
JUPITER_TOKENS_LIST_API = "https://token.jup.ag/strict"


def fetch_jupiter_tokens():
    logging.info("Fetching %s ...", JUPITER_TOKENS_LIST_API)
    try:
        response = requests.get(JUPITER_TOKENS_LIST_API)
        response.raise_for_status()
        logging.info("Fetched.")
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from Jupiter API: {e}")
        return None


def save_tokens_to_file(tokens):
    token_dict = {token['address']: token['symbol'] for token in tokens}
    today = datetime.now().strftime("%Y%m%d")
    filename = os.path.join(TOKEN_LISTS_DIR, f"jupiter.{today}.json")

    with open(filename, 'w') as file:
        json.dump(token_dict, file, indent=4)

    logging.info("Wrote to %s", filename)


def main():
    tokens = fetch_jupiter_tokens()
    if tokens:
        save_tokens_to_file(tokens)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
