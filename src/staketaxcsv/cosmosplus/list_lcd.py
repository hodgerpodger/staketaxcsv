""" usage: python3 staketaxcsv/cosmosplus/list_lcd.py

Stand-alone script to retrieves all LCD endpoints from https://github.com/cosmos/chain-registry
into a file (list_lcd.json).
"""

import logging
import glob
import json
import os
import requests
import tempfile
import time
import zipfile
logging.basicConfig(level=logging.INFO)
CHAIN_REGISTRY_URL = "https://github.com/cosmos/chain-registry/archive/refs/heads/master.zip"
OUTPUT_LCD_JSON = os.path.dirname(os.path.abspath(__file__)) + "/list_lcd.json"


def main():
    tempdir = download_repo()
    extract_lcds(tempdir)


def download_repo():
    """ Downloads contents of https://github.com/cosmos/chain-registry to local files """
    tempdir = tempfile.gettempdir() + "/list_lcd_" + str(int((time.time())))
    os.mkdir(tempdir)
    zfile = tempdir + "/" + "file.zip"

    # Download https://github.com/cosmos/chain-registry contents as .zip
    logging.info("Retrieving %s ... ", CHAIN_REGISTRY_URL)
    response = requests.get(CHAIN_REGISTRY_URL)
    with open(zfile, 'wb') as f:
        f.write(response.content)
    logging.info("Wrote to %s", zfile)

    # Extract files
    with zipfile.ZipFile(zfile, 'r') as zip_ref:
        zip_ref.extractall(tempdir)

    return tempdir


def extract_lcds(directory):
    """ Extracts lcd endpoint string from local files.  Writes result to list_lcd.json """
    pattern = directory + "/chain-registry-master/*/chain.json"
    matching_files = glob.glob(pattern)

    out = {}
    for json_file in sorted(matching_files):
        # Extract chain name
        chain_name = json_file.split("/")[-2]

        # Extract lcd rest endpoints
        with open(json_file, 'r') as f:
            data = json.load(f)
        if "apis" in data and "rest" in data["apis"]:
            addresses = [item["address"] for item in data["apis"]["rest"]]
        else:
            addresses = []

        out[chain_name] = addresses

    with open(OUTPUT_LCD_JSON, 'w') as f:
        json.dump(out, f, indent=4)
    logging.info("Wrote to %s", OUTPUT_LCD_JSON)


if __name__ == "__main__":
    main()
