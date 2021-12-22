
from common.TxInfo import TxInfo
from osmo.constants import EXCHANGE_OSMOSIS, CUR_OSMO


class TxInfoOsmo(TxInfo):
    """ Osmosis transaction info """

    def __init__(self, txid, timestamp, fee, wallet_address, msgs):
        url = "https://mintscan.io/osmosis/txs/{}".format(txid)
        super().__init__(txid, timestamp, fee, CUR_OSMO, wallet_address, EXCHANGE_OSMOSIS, url)

        self.msgs = msgs

    def print(self):
        print("txid: {}".format(self.txid))
        print("timestamp: {}".format(self.timestamp))
        print("fee: {}".format(self.fee))

        i = 0
        for i, msg in enumerate(self.msgs):
            print("\nmsg{}:".format(i))
            print("\tmessage: {}".format(msg.message))
            print("\ttransfers_in: {}".format(msg.transfers[0]))
            print("\ttransfers_out: {}".format(msg.transfers[1]))
            i += 1
        print("\n")


class MsgInfo:
    """ Single message info for index <i> """

    def __init__(self, message, transfers, row_txid):
        self.message = message
        self.transfers = transfers
        self.row_txid = row_txid
