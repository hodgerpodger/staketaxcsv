

import pprint

import staketaxcsv.common.ibc.constants
from staketaxcsv.common.TxInfo import TxInfo


class TxInfoIBC(TxInfo):

    def __init__(self, txid, timestamp, fee, fee_currency, wallet_address, msgs, mintscan_label, memo):
        url = "https://mintscan.io/{}/txs/{}".format(mintscan_label, txid)
        exchange = "{}_blockchain".format(mintscan_label)
        super().__init__(txid, timestamp, fee, fee_currency, wallet_address, exchange, url)
        self.msgs = msgs
        self.memo = memo

    def print(self):
        for i, msg in enumerate(self.msgs):
            print("\nmsg{}:".format(i))
            print("\tmsg_type: {}".format(msg.msg_type))
            print("\tcontract: {}".format(msg.contract))
            print("\ttransfers_in: {}".format(msg.transfers[0]))
            print("\ttransfers_out: {}".format(msg.transfers[1]))
            print("\n\tmessage:")
            pprint.pprint(msg.message)
            print("\n\twasm:")
            pprint.pprint(msg.wasm)
        print("\n")

    def is_execute_contract(self):
        if self.msgs and self.msgs[0].msg_type == common.ibc.constants.MSG_TYPE_EXECUTE_CONTRACT:
            return True
        else:
            return False
