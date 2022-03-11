
from atom.constants import CUR_ATOM
from common.TxInfo import TxInfo
import pprint


class TxInfoIBC(TxInfo):

    def __init__(self, txid, timestamp, fee, fee_currency, wallet_address, msgs, mintscan_label, exchange):
        url = "https://www.mintscan.io/{}/txs/{}".format(mintscan_label, txid)
        super().__init__(txid, timestamp, fee, fee_currency, wallet_address, exchange, url)
        self.msgs = msgs

    def print(self):
        for i, msg in enumerate(self.msgs):
            print("\nmsg{}:".format(i))
            pprint.pprint(msg.message)
            print("\tmsg_type: {}".format(msg.msg_type))
            print("\ttransfers_in: {}".format(msg.transfers[0]))
            print("\ttransfers_out: {}".format(msg.transfers[1]))
        print("\n")
