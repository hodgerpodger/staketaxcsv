import pprint

from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.common.TxInfo import TxInfo
from staketaxcsv.fet import constants as co
from staketaxcsv.fet.fetchhub1 import constants as co2


class TxInfoFet(TxInfo):
    """ Osmosis transaction info """

    def __init__(self, txid, timestamp, fee, wallet_address, msgs):
        url = "https://mintscan.io/{}/txs/{}".format(co.MINTSCAN_LABEL_FET, txid)
        fee_currency = co2.CUR_FET if fee else ""
        super().__init__(txid, timestamp, fee, fee_currency, wallet_address, co.EXCHANGE_FET, url)

        self.msgs = msgs

    def print(self):
        print("txid: {}".format(self.txid))
        print("timestamp: {}".format(self.timestamp))
        print("fee: {}".format(self.fee))

        for i, msg in enumerate(self.msgs):
            print("\nmsg{}:".format(i))
            print("\tmsg_type: {}".format(msg.msg_type))
            print("\tcontract: {}".format(msg.contract))
            print("\ttransfers_in: {}".format(msg.transfers[0]))
            print("\ttransfers_out: {}".format(msg.transfers[1]))
            print("\tmessage:")
            pprint.pprint(msg.message)
            print("\n\twasm:")
            pprint.pprint(msg.wasm)
        print("\n")

    def first_msg_type(self):
        if self.msgs:
            return self.msgs[0].msg_type
        else:
            return None

    def is_execute_contract(self):
        if self.msgs and self.msgs[0].msg_type == co2.ACTION_TYPE_EXECUTE:
            return True
        else:
            return False


class MsgInfo:
    """ Single message info for index <i> """

    def __init__(self, msg_index, msg_type, message, transfers, log):
        self.msg_index = msg_index
        self.msg_type = msg_type
        self.message = message
        self.transfers = transfers
        self.log = log
        self.wasm = MsgInfoIBC.wasm(log)
        self.contract = self._contract(message)

    def _contract(self, message):
        if message and message.get("contract_address"):
            return message.get("contract_address")
        else:
            return None
