# Documentation
# https://developer.algorand.org/docs/get-details/transactions/
# https://developer.algorand.org/docs/get-details/transactions/transactions/
# https://github.com/algorand/go-algorand
import base64

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.export_tx import export_receive_tx, export_reward_tx, export_send_tx
from staketaxcsv.algo.handle_folks import is_folks_escrow_address
from staketaxcsv.algo.handle_simple import handle_participation_rewards, handle_unknown
from staketaxcsv.algo.util_algo import get_transaction_note

# Algostake escrow wallet: https://algostake.org/litepaper
ADDRESS_ALGOSTAKE_ESCROW = "4ZK3UPFRJ643ETWSWZ4YJXH3LQTL2FUEI6CIT7HEOVZL6JOECVRMPP34CY"

ADDRESS_ALGOMINT = "ETGSQKACKC56JWGMDAEP5S2JVQWRKTQUVKCZTMPNUGZLDVCWPY63LSI3H4"

ADDRESS_PACT_REWARDS = "PACTC5CQVKK6F43TPYII2WED72BXYIQ5OF7DKQREDOY4UXCYJRMGGQ5IQQ"

ADDRESS_FOLKS_REWARDS = "OW3VJ3YSECTNTJ73GNQE2LYOQUMMAV577NDNF53SXRKB33OST6NNTPRD4Y"


def is_governance_reward_transaction(wallet_address, group):
    if len(group) != 1:
        return False

    transaction = group[0]
    if transaction["tx-type"] != "pay":
        return False

    if transaction[co.TRANSACTION_KEY_PAYMENT]["receiver"] != wallet_address:
        return False

    note = get_transaction_note(transaction)
    if note is None:
        return False

    if "af/gov" not in note:
        return False

    return True


def handle_governance_reward_transaction(group, exporter, txinfo):
    transaction = group[0]
    payment_details = transaction[co.TRANSACTION_KEY_PAYMENT]

    txinfo.txid = transaction["id"]
    reward = Algo(payment_details["amount"] + transaction["receiver-rewards"])
    export_reward_tx(exporter, txinfo, reward, comment="Governance")


def handle_payment_transaction(wallet_address, transaction, exporter, txinfo):
    payment_details = transaction[co.TRANSACTION_KEY_PAYMENT]
    asset_id = 0

    _handle_transfer(wallet_address, transaction, payment_details, exporter, txinfo, asset_id)


def handle_asa_transaction(wallet_address, transaction, exporter, txinfo):
    transfer_details = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
    asset_id = transfer_details["asset-id"]

    _handle_transfer(wallet_address, transaction, transfer_details, exporter, txinfo, asset_id)


def has_only_transfer_transactions(transactions):
    return len([tx for tx in transactions
        if (tx["tx-type"] == co.TRANSACTION_TYPE_PAYMENT
            or tx["tx-type"] == co.TRANSACTION_TYPE_ASSET_TRANSFER)]) == len(transactions)


def handle_transfer_transactions(wallet_address, transactions, exporter, txinfo):
    for transaction in transactions:
        txtype = transaction["tx-type"]
        if txtype == co.TRANSACTION_TYPE_PAYMENT:
            handle_payment_transaction(wallet_address, transaction, exporter, txinfo)
        elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
            handle_asa_transaction(wallet_address, transaction, exporter, txinfo)
        else:
            handle_unknown(exporter, txinfo)


def _handle_transfer(wallet_address, transaction, details, exporter, txinfo, asset_id):
    txsender = transaction["sender"]
    txreceiver = details["receiver"]
    close_to = details.get("close-to", details.get("close-remainder-to", None))
    rewards_amount = 0

    if wallet_address not in [txsender, txreceiver, close_to]:
        return handle_unknown(exporter, txinfo)

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
        receive_asset = Asset(asset_id, receive_amount - send_amount)
        if not receive_asset.zero():
            row = None
            if txsender == ADDRESS_ALGOSTAKE_ESCROW:
                export_reward_tx(exporter, txinfo, receive_asset, comment="Algostake")
            elif txsender == ADDRESS_PACT_REWARDS:
                export_reward_tx(exporter, txinfo, receive_asset, comment="Pact")
            else:
                note = get_transaction_note(transaction)
                if note is not None and "tinymanStaking/v1" in note:
                    export_reward_tx(exporter, txinfo, receive_asset, comment="Tinyman")
                elif txsender == ADDRESS_FOLKS_REWARDS and note == "Folks Finance fStaking rewards":
                    export_reward_tx(exporter, txinfo, receive_asset, comment="Folks Finance")
                else:
                    export_receive_tx(
                        exporter, txinfo, receive_asset, fee_amount,
                        "Algomint" if txsender == ADDRESS_ALGOMINT else None)
    else:
        rewards_amount += transaction["sender-rewards"]
        if close_to and txreceiver != close_to:
            # We are closing the account, but sending the remaining balance is sent to different address
            close_asset = Asset(asset_id, details["close-amount"])
            export_send_tx(exporter, txinfo, close_asset)

            send_asset = Asset(asset_id, details["amount"])
            export_send_tx(exporter, txinfo, send_asset, transaction["fee"], txreceiver)
        else:
            # Regular send or closing to the same account
            send_asset = Asset(asset_id, details["amount"] + details["close-amount"])

            # Ignore Folks transactions to increase collateral with fTokens
            if not is_folks_escrow_address(txreceiver):
                export_send_tx(
                    exporter, txinfo, send_asset, transaction["fee"], txreceiver,
                    "Algomint" if txreceiver == ADDRESS_ALGOMINT else None)

    reward = Algo(rewards_amount)
    handle_participation_rewards(reward, exporter, txinfo)
