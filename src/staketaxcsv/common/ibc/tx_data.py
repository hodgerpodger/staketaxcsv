"""

Simpler wrapper interface to get transaction data

"""

import logging

from staketaxcsv.common.ibc import api_mintscan_v1, api_lcd, api_rpc, api_rpc_multinode
from staketaxcsv.common.ibc.api_mintscan_v1 import MintscanAPI


class TxDataLcd:

    def __init__(self, lcd_node, max_txs, limit_per_query=None):
        self.lcd_node = lcd_node
        self.max_txs = max_txs
        self.api = api_lcd.make_lcd_api(lcd_node)
        self.limit_per_query = limit_per_query

    def get_tx(self, txid):
        return self.api.get_tx(txid)

    def get_txs_all(self, address, progress, start_date=None, end_date=None):
        # only include optional parameter limit if defined
        kwargs = {}
        if self.limit_per_query:
            kwargs["limit"] = self.limit_per_query

        return api_lcd.get_txs_all(self.lcd_node, address, self.max_txs, progress=progress, **kwargs)

    def get_txs_pages_count(self, address, start_date=None, end_date=None):
        # only include optional parameter limit if defined
        kwargs = {}
        if self.limit_per_query:
            kwargs["limit"] = self.limit_per_query

        return api_lcd.get_txs_pages_count(self.lcd_node, address, self.max_txs, **kwargs)


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


class TxDataRpc:

    def __init__(self, rpc_nodes, max_txs):
        self.rpc_nodes = rpc_nodes
        self.max_txs = max_txs

    def get_tx(self, txid):
        return api_rpc_multinode.get_tx(self.rpc_nodes, txid)

    def get_txs_all(self, address, progress_rpc, limit=api_rpc.TXS_LIMIT_PER_QUERY):
        return api_rpc_multinode.get_txs_all(
            self.rpc_nodes, address, self.max_txs, progress_rpc=progress_rpc, limit=limit)

    def get_txs_pages_count(self, address, progress_rpc=None, limit=api_rpc.TXS_LIMIT_PER_QUERY):
        return api_rpc_multinode.get_txs_pages_count(
            self.rpc_nodes, address, self.max_txs, progress_rpc=progress_rpc, limit=limit)
