from common.TxInfo import TxInfo
from terra.constants import EXCHANGE_TERRA_BLOCKCHAIN
import pprint


class TxInfoTerra(TxInfo):
    """ Terra transaction info """

    def __init__(self, txid, timestamp, fee, fee_currency, wallet_address, msgs):
        url = "https://finder.terra.money/mainnet/tx/{}".format(txid)
        super().__init__(txid, timestamp, fee, fee_currency, wallet_address, EXCHANGE_TERRA_BLOCKCHAIN, url)

        self.msgs = msgs

    def print(self):
        print("\nTXINFO\n")
        print("txid: {}".format(self.txid))
        print("timestamp: {}".format(self.timestamp))
        print("fee: {}".format(self.fee))

        for msg in self.msgs:
            msg.print()

        print("\n")


class MsgInfo:

    def __init__(self, msg_index, execute_msg, transfers, log, actions, contract):
        self.msg_index = msg_index
        self.execute_msg = execute_msg
        self.transfers = transfers
        self.log = log
        self.actions = actions
        self.contract = contract

    def print(self):
        print("\nmsg{}:".format(self.msg_index))
        print("\tcontract: {}".format(self.contract))
        print("\ttransfers_in: {}".format(self.transfers[0]))
        print("\ttransfers_out: {}".format(self.transfers[1]))
        print("\texecute_msg: ")
        pprint.pprint(self.execute_msg)
        print("\tactions:")
        pprint.pprint(self.actions)
