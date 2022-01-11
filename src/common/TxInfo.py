class TxInfo:

    def __init__(self, txid, timestamp, fee, fee_currency, wallet_address, exchange, url):
        self.txid = txid
        self.timestamp = timestamp
        self.fee = fee
        self.fee_currency = fee_currency
        self.wallet_address = wallet_address
        self.exchange = exchange
        self.url = url
        self.comment = ""
