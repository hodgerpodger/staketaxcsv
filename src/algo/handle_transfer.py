# Documentation
# https://developer.algorand.org/docs/get-details/transactions/
# https://developer.algorand.org/docs/get-details/transactions/transactions/
# https://github.com/algorand/go-algorand
import base64

from algo import constants as co
from algo.asset import Algo, Asset
from algo.handle_simple import handle_participation_rewards
from common.make_tx import make_reward_tx, make_transfer_in_tx, make_transfer_out_tx

# Algostake escrow wallet: https://algostake.org/litepaper
ADDRESS_ALGOSTAKE_ESCROW = "4ZK3UPFRJ643ETWSWZ4YJXH3LQTL2FUEI6CIT7HEOVZL6JOECVRMPP34CY"


def is_governance_reward_transaction(wallet_address, group):
    if len(group) != 1:
        return False

    transaction = group[0]
    if transaction["tx-type"] != "pay":
        return False

    if transaction[co.TRANSACTION_KEY_PAYMENT]["receiver"] != wallet_address:
        return False

    if "note" not in transaction:
        return False

    try:
        note = base64.b64decode(transaction["note"]).decode("utf-8")
    except Exception:
        return False

    if "af/gov" not in note:
        return False

    return True


def handle_governance_reward_transaction(group, exporter, txinfo):
    transaction = group[0]
    payment_details = transaction[co.TRANSACTION_KEY_PAYMENT]

    reward = Algo(payment_details["amount"] + transaction["receiver-rewards"])
    txinfo.txid = transaction["id"]
    txinfo.comment = "Governance"
    row = make_reward_tx(txinfo, reward, reward.ticker)
    exporter.ingest_row(row)


def handle_payment_transaction(wallet_address, transaction, exporter, txinfo):
    payment_details = transaction[co.TRANSACTION_KEY_PAYMENT]
    asset_id = 0

    _handle_transfer(wallet_address, transaction, payment_details, exporter, txinfo, asset_id)


def handle_asa_transaction(wallet_address, transaction, exporter, txinfo):
    transfer_details = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
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
        fee_amount = 0
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
            fee_amount = transaction["fee"]
        amount = Asset(asset_id, receive_amount - send_amount)
        if not amount.zero():
            row = None
            if txsender == ADDRESS_ALGOSTAKE_ESCROW:
                row = make_reward_tx(txinfo, amount, amount.ticker)
                row.comment = "Algostake"
            else:
                row = make_transfer_in_tx(txinfo, amount, amount.ticker)
                fee = Algo(fee_amount)
                row.fee = fee.amount
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
                fee = Algo(transaction["fee"])
                row.fee = fee.amount
                exporter.ingest_row(row)
        else:
            # Regular send or closing to the same account
            send_amount = Asset(asset_id, details["amount"] + details["close-amount"])

            if not send_amount.zero():
                row = make_transfer_out_tx(txinfo, send_amount, send_amount.ticker, txreceiver)
                fee = Algo(transaction["fee"])
                row.fee = fee.amount
                exporter.ingest_row(row)

    reward = Algo(rewards_amount)
    handle_participation_rewards(reward, exporter, txinfo)
