"""

TxData wrapper class to get transaction data, so that it is easy to switch between
LCD and mintscan transaction data, as needed.

"""
import logging

from staketaxcsv.settings_csv import MINTSCAN_DATA_TICKERS
from staketaxcsv.common.ibc import api_mintscan_v1, api_lcd
from staketaxcsv.common.ibc.api_mintscan_v1 import MintscanAPI


class TxData:

    def __init__(self, ticker, lcd_node, max_txs):
        self.ticker = ticker
        self.lcd_node = lcd_node
        self.max_txs = max_txs
        self.use_mintscan = self._use_mintscan(ticker)
        self.mintscan_api = MintscanAPI(ticker) if self.use_mintscan else None
        self.lcd_api = api_lcd.make_lcd_api(lcd_node) if not self.use_mintscan else None

    def _use_mintscan(self, ticker):
        if ticker in MINTSCAN_DATA_TICKERS:
            logging.info("Using mintscan data ...")
            return True
        else:
            logging.info("Using lcd data ...")
            return False

    def get_tx(self, txid):
        if self.use_mintscan:
            return self.mintscan_api.get_tx(txid)
        else:
            return self.lcd_api.get_tx(txid)

    def get_txs_all(self, address, progress, start_date=None, end_date=None):
        if self.use_mintscan:
            return api_mintscan_v1.get_txs_all(
                self.ticker, address, self.max_txs, progress=progress, start_date=start_date, end_date=end_date)
        else:
            # lcd data version
            if start_date or end_date:
                logging.error("LCD get_txs_all() does not support start_date or end_date parameter")
            return api_lcd.get_txs_all(self.lcd_node, address, self.max_txs, progress=progress)

    def get_txs_pages_count(self, address, start_date=None, end_date=None):
        if self.use_mintscan:
            return api_mintscan_v1.get_txs_page_count(
                self.ticker, address, self.max_txs, start_date=start_date, end_date=end_date)
        else:
            # lcd data version
            if start_date or end_date:
                logging.error("LCD get_txs_pages_count() does not support start_date or end_date parameter")
            return api_lcd.get_txs_pages_count(self.lcd_node, address, self.max_txs)

    def account_exists(self, address):
        return api_lcd.make_lcd_api(self.lcd_node).account_exists(address)
