from staketaxcsv.algo import constants as co
from staketaxcsv.algo.export_tx import export_reward_tx
from staketaxcsv.algo.util_algo import get_transfer_asset, get_transfer_receiver
from staketaxcsv.common.make_tx import make_unknown_tx, make_unknown_tx_with_transfer


def handle_unknown(exporter, txinfo):
    row = make_unknown_tx(txinfo)
    exporter.ingest_row(row)


def handle_unknown_transactions(transactions, wallet_address, exporter, txinfo):
    for transaction in transactions:
        txtype = transaction["tx-type"]
        if txtype == co.TRANSACTION_KEY_PAYMENT or txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
            txsender = transaction["sender"]
            txreceiver = get_transfer_receiver(transaction)
            asset = get_transfer_asset(transaction)
            if txsender == wallet_address:
                row = make_unknown_tx_with_transfer(txinfo, asset.amount, asset.ticker, "", "")
                exporter.ingest_row(row)
            elif txreceiver == wallet_address:
                row = make_unknown_tx_with_transfer(txinfo, "", "", asset.amount, asset.ticker)
                exporter.ingest_row(row)
        elif txtype == co.TRANSACTION_TYPE_APP_CALL:
            inner_transactions = transaction.get("inner-txns", [])
            handle_unknown_transactions(inner_transactions, wallet_address, exporter, txinfo)


def handle_participation_rewards(reward, exporter, txinfo):
    export_reward_tx(exporter, txinfo, reward, comment="Participation Rewards")
