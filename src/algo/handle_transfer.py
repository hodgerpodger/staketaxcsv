# Documentation
# https://developer.algorand.org/docs/get-details/transactions/
# https://developer.algorand.org/docs/get-details/transactions/transactions/
# https://github.com/algorand/go-algorand
import base64

from algo.asset import Algo, Asset
from common.make_tx import make_reward_tx, make_transfer_in_tx, make_transfer_out_tx


def is_governance_reward_transaction(wallet_address, group):
    if len(group) != 1:
        return False

    transaction = group[0]
    if transaction["tx-type"] != "pay":
        return False

    if transaction["payment-transaction"]["receiver"] != wallet_address:
        return False

    if "note" not in transaction:
        return False

    note = base64.b64decode(transaction["note"]).decode("utf-8")
    if "af/gov" not in note:
        return False

    return True


def handle_governance_reward_transaction(group, exporter, txinfo):
    transaction = group[0]
    payment_details = transaction["payment-transaction"]

    reward = Algo(payment_details["amount"] + transaction["receiver-rewards"])
    txinfo.txid = transaction["id"]
    txinfo.comment = "Governance"
    row = make_reward_tx(txinfo, reward, reward.ticker)
    exporter.ingest_row(row)


def handle_payment_transaction(wallet_address, transaction, exporter, txinfo):
    payment_details = transaction["payment-transaction"]
    asset_id = 0

    _handle_transfer(wallet_address, transaction, payment_details, exporter, txinfo, asset_id)


def handle_asa_transaction(wallet_address, transaction, exporter, txinfo):
    transfer_details = transaction["asset-transfer-transaction"]
    asset_id = transfer_details["asset-id"]

    _handle_transfer(wallet_address, transaction, transfer_details, exporter, txinfo, asset_id)


def _handle_transfer(wallet_address, transaction, details, exporter, txinfo, asset_id):
    txsender = transaction["sender"]
    txreceiver = details["receiver"]
    close_to = details.get("close-to", details.get("close-remainder-to", None))
    rewards_amount = 0

    if txreceiver == wallet_address or close_to == wallet_address:
        receive_amount = 0
        send_amount = 0
        # We could be all receiver, sender and close-to account
        if txreceiver == wallet_address:
            receive_amount += details["amount"]
            rewards_amount += transaction["receiver-rewards"]
        # A closed account sent us their remaining balance
        if close_to == wallet_address:
            receive_amount += details["close-amount"]
            rewards_amount += transaction["close-rewards"]
        # A transaction to self was commonly used for compounding rewards
        if txsender == wallet_address:
            send_amount += details["amount"]
            rewards_amount += transaction["sender-rewards"]
        amount = Asset(asset_id, receive_amount - send_amount)
        if not amount.zero():
            row = make_transfer_in_tx(txinfo, amount, amount.ticker)
            exporter.ingest_row(row)
    else:
        rewards_amount += transaction["sender-rewards"]
        if close_to and txreceiver != close_to:
            # We are closing the account, but sending the remaining balance is sent to different address
            close_amount = Asset(asset_id, details["close-amount"])
            row = make_transfer_out_tx(txinfo, close_amount, close_amount.ticker, close_to)
            row.fee = 0
            exporter.ingest_row(row)
            send_amount = Asset(asset_id, details["amount"])

            if not send_amount.zero():
                row = make_transfer_out_tx(txinfo, send_amount, send_amount.ticker, txreceiver)
                row.fee = Algo(transaction["fee"])
                exporter.ingest_row(row)
        else:
            # Regular send or closing to the same account
            send_amount = Asset(asset_id, details["amount"] + details["close-amount"])

            if not send_amount.zero():
                row = make_transfer_out_tx(txinfo, send_amount, send_amount.ticker, txreceiver)
                row.fee = Algo(transaction["fee"])
                exporter.ingest_row(row)
        txinfo.fee = 0

    if rewards_amount > 0:
        reward = Algo(rewards_amount)
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)
