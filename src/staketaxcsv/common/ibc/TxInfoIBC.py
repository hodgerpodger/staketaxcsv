

import pprint

import staketaxcsv.common.ibc.constants as co
from staketaxcsv.common.TxInfo import TxInfo


class TxInfoIBC(TxInfo):

    def __init__(self, txid, timestamp, fee, fee_currency, wallet_address, msgs, mintscan_label, memo, is_failed):
        url = "https://mintscan.io/{}/txs/{}".format(mintscan_label, txid)
        exchange = "{}_blockchain".format(mintscan_label)
        super().__init__(txid, timestamp, fee, fee_currency, wallet_address, exchange, url)
        self.msgs = msgs
        self.memo = memo
        self.is_failed = is_failed

    def print(self):
        for i, msg in enumerate(self.msgs):
            msg.print()
        print("\n")

    def is_execute_contract(self):
        if self.msgs and self.msgs[0].msg_type == co.MSG_TYPE_EXECUTE_CONTRACT:
            return True
        else:
            return False
