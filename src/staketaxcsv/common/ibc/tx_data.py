"""

Simpler wrapper interface to get transaction data

"""

import logging

from staketaxcsv.common.ibc import api_mintscan_v1, api_lcd
from staketaxcsv.common.ibc.api_mintscan_v1 import MintscanAPI


class TxDataLCD:

    def __init__(self, lcd_node, max_txs):
        self.lcd_node = lcd_node
        self.max_txs = max_txs
        self.api = api_lcd.make_lcd_api(lcd_node)

    def get_tx(self, txid):
        return self.api.get_tx(txid)

    def get_txs_all(self, address, progress):
        return api_lcd.get_txs_all(self.lcd_node, address, self.max_txs, progress=progress)

    def get_txs_pages_count(self, address):
        return api_lcd.get_txs_pages_count(self.lcd_node, address, self.max_txs)


class TxDataMintscan:

    def __init__(self, ticker, max_txs):
        self.ticker = ticker
        self.max_txs = max_txs
        self.api = MintscanAPI(ticker)

    def get_tx(self, txid):
        return self.api.get_tx(txid)

    def get_txs_all(self, address, progress, start_date=None, end_date=None):
        return api_mintscan_v1.get_txs_all(
            self.ticker, address, self.max_txs, progress=progress, start_date=start_date, end_date=end_date)

    def get_txs_pages_count(self, address, start_date=None, end_date=None):
        return api_mintscan_v1.get_txs_page_count(
            self.ticker, address, self.max_txs, start_date=start_date, end_date=end_date)
