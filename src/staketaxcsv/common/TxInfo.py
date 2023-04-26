class TxInfo:

    def __init__(self, txid, timestamp, fee, fee_currency, wallet_address, exchange, url, block_svc_hash=''):
        self.txid = txid
        self.timestamp = timestamp
        self.fee = fee
        self.fee_currency = fee_currency
        self.wallet_address = wallet_address
        self.exchange = exchange
        self.url = url
        self.comment = ""
        self.memo = ""
        self.block_svc_hash = block_svc_hash
