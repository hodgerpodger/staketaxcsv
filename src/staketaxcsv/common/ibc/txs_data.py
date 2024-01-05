"""

API wrapper to get transaction data.  Wrapper so that it is easy to switch between LCD and mintscan, as needed.

"""
import logging

from staketaxcsv.settings_csv import MINTSCAN_DATA_ENABLED_FOR_TICKERS
from staketaxcsv.common.ibc import api_mintscan_v1, api_lcd
TICKERS_ENABLED = MINTSCAN_DATA_ENABLED_FOR_TICKERS.split(",")


def get_txs_all(ticker, address, max_txs, progress=None, from_date=None, to_date=None, lcd_node=None):
    # TODO: untested

    if _use_mintscan(ticker):
        return api_mintscan_v1.get_txs_all(ticker, address, max_txs, progress=progress, from_date=from_date,
                                           to_date=to_date)
    else:
        # use lcd data

        if from_date or to_date:
            logging.error("LCD get_txs_all() does not support from_date or to_date parameter.  "
                          "Proceeding with all time.")
        if not lcd_node:
            raise Exception("Missing lcd_node in txs_data.get_txs_all()")

        return api_lcd.get_txs_all(lcd_node, address, max_txs, progress=progress)


def get_txs_pages_count():
    # TODO: untested
    pass


def _use_mintscan(ticker):
    if ticker in TICKERS_ENABLED:
        logging.info("Using mintscan data ...")
        return True
    else:
        logging.info("Using lcd data ...")
        return False
