from huahua.constants import CUR_HUAHUA, EXCHANGE_CHIHUAHUA_BLOCKCHAIN
from common.TxInfo import TxInfo


class TxInfoHuahua(TxInfo):

    def __init__(self, txid, timestamp, fee, wallet_address, url):
        super().__init__(txid, timestamp, fee, CUR_HUAHUA, wallet_address, EXCHANGE_CHIHUAHUA_BLOCKCHAIN, url)
