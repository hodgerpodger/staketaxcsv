import glob
import json
import logging
import os

TOKEN_LISTS_DIR = os.path.dirname(os.path.realpath(__file__)) + "/token_lists"


class Tickers:
    loaded = False
    tickers = {}

    @classmethod
    def _load(cls):
        if cls.loaded is False:
            json_files = glob.glob(os.path.join(TOKEN_LISTS_DIR, '*.json'))

            # Extract dates from filenames and sort files by date
            file_date_pairs = []
            for file in json_files:
                # Extract date part from filename
                date_part = file.split('.')[-2]
                if date_part.isdigit() and len(date_part) == 8:
                    file_date_pairs.append((file, date_part))

            file_date_pairs.sort(key=lambda x: x[1])

            # Load the JSON files in sorted order
            for file, _ in file_date_pairs:
                try:
                    with open(file, 'r') as json_file:
                        data = json.load(json_file)
                        for address, symbol in data.items():
                            cls.tickers.setdefault(address, symbol)
                    logging.info("Loaded tickers json file = %s", json_file)
                except Exception as e:
                    logging.error(f"Error loading file {file}: {str(e)}")

            cls.loaded = True

    @classmethod
    def get(cls, address):
        cls._load()

        ticker = cls.tickers.get(address, None)
        if ticker:
            return ticker
        else:
            return address
