
from common.TxInfo import TxInfo
import pprint
from osmo.constants import EXCHANGE_OSMOSIS, CUR_OSMO
from osmo import util_osmo


class TxInfoOsmo(TxInfo):
    """ Common properties across every blockchain transaction (only) """

    def __init__(self, txid, timestamp, fee, wallet_address):
        url = "https://mintscan.io/osmosis/txs/{}".format(txid)
        super().__init__(txid, timestamp, fee, CUR_OSMO, wallet_address, EXCHANGE_OSMOSIS, url)

        self.msgs = None

    def print(self):
        print("txid: {}".format(self.txid))
        print("timestamp: {}".format(self.timestamp))
        print("fee: {}".format(self.fee))

        i = 0
        for msg, transfers in self.msgs:
            print("\nmsg{}:".format(i))
            print("\tmessage: {}".format(msg))
            print("\ttransfers_in: {}".format(transfers[0]))
            print("\ttransfers_out: {}".format(transfers[1]))
            i += 1
        print("\n")
