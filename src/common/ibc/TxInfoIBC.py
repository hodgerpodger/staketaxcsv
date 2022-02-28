
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
            print("\ttransfers_in: {}".format(msg.transfers[0]))
            print("\ttransfers_out: {}".format(msg.transfers[1]))
        print("\n")


class MsgInfoIBC:
    """ Single message info for index <i> """

    def __init__(self, msg_index, message, log, transfers, transfer_event):
        self.msg_index = msg_index
        self.message = message
        self.log = log
        self.transfers = transfers
        self.transfer_event = transfer_event
