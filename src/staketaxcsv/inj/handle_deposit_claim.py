import logging

from staketaxcsv.common.ibc import make_tx
from staketaxcsv.common.ExporterTypes import TX_TYPE_DUPLICATE_DEPOSIT_CLAIM
from staketaxcsv.inj import constants as co


class Deposits:

    txs = {}

    @classmethod
    def _key(cls, message):
        cosmos_receiver = message["cosmos_receiver"]
        event_nonce = message["event_nonce"]
        block_height = message["block_height"]
        ethereum_sender = message["ethereum_sender"]

        return event_nonce, block_height, ethereum_sender, cosmos_receiver

    @classmethod
    def key_as_string(cls, message):
        k = cls._key(message)
        return f"deposit_claim [nonce={k[0]}, height={k[1]}, sender={k[2]}, receiver={k[3]}]"

    @classmethod
    def exists(cls, message):
        logging.info("Deposits.exists(): message", message)
        k = cls._key(message)
        return k in cls.txs

    @classmethod
    def add(cls, message):
        k = cls._key(message)
        cls.txs[k] = message


def handle_deposit_claim(exporter, txinfo, msginfo):
    message = msginfo.message
    wallet_address = exporter.wallet_address

    cosmos_receiver = message["cosmos_receiver"]
    comment = Deposits.key_as_string(message)

    if cosmos_receiver == wallet_address:
        if Deposits.exists(message):
            row = make_tx.make_simple_tx(txinfo, msginfo, tx_type=TX_TYPE_DUPLICATE_DEPOSIT_CLAIM)
            row.comment += comment
            exporter.ingest_row(row)
        else:
            amount_raw = message["amount"]
            amount = float(amount_raw) / co.EXP_18
            currency = co.CURRENCY_INJ

            row = make_tx.make_transfer_in_tx(txinfo, msginfo, amount, currency)
            row.comment += comment
            exporter.ingest_row(row)

            Deposits.add(message)
    else:
        row = make_tx.make_noop_tx(txinfo, msginfo)
        row.comment += f"deposit claim for foreign wallet (cosmos_receiver={cosmos_receiver}"
        exporter.ingest_row(row)
