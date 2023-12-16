"""
usage: python3 staketaxcsv/sol/tickers/gather/solana_tokenlist.py

* Writes tickers json file to staketaxcsv/sol/tickers/token_lists/solana_tokenlist.YYYYMMDD.json

"""
import json
import logging
import os
from datetime import datetime
from staketaxcsv.sol.tickers.tickers import TOKEN_LISTS_DIR

# From https://github.com/solana-labs/token-list/blob/main/src/tokens/solana.tokenlist.json
# https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json
TOKEN_LIST_JSON = os.path.dirname(os.path.realpath(__file__)) + "/solana.tokenlist.json"


def read_solana_token_list():
    try:
        with open(TOKEN_LIST_JSON, 'r') as file:
            data = json.load(file)
        return data['tokens']
    except FileNotFoundError:
        logging.error("File %s not found", TOKEN_LIST_JSON)
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON from the file")
        return None


def save_tokens_to_file(tokens):
    token_dict = {token['address']: token['symbol'] for token in tokens}
    today = datetime.now().strftime("%Y%m%d")
    filename = os.path.join(TOKEN_LISTS_DIR, f"solana_tokenlist.{today}.json")

    with open(filename, 'w') as file:
        json.dump(token_dict, file, indent=4)
    logging.info("Wrote to %s", filename)


def main():
    tokens = read_solana_token_list()
    if tokens:
        save_tokens_to_file(tokens)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
