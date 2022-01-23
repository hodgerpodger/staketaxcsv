from atom.constants import CUR_ATOM, EXCHANGE_COSMOS_BLOCKCHAIN
from common.TxInfo import TxInfo


class TxInfoAtom(TxInfo):

    def __init__(self, txid, timestamp, fee, wallet_address, url, chain_id):
        super().__init__(txid, timestamp, fee, CUR_ATOM, wallet_address, EXCHANGE_COSMOS_BLOCKCHAIN, url)
        self.chain_id = chain_id
