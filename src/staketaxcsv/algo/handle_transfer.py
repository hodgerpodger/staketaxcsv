# Documentation
# https://developer.algorand.org/docs/get-details/transactions/
# https://developer.algorand.org/docs/get-details/transactions/transactions/
# https://github.com/algorand/go-algorand

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.export_tx import (
    export_participation_rewards,
    export_receive_tx,
    export_reward_tx,
    export_send_tx,
    export_spend_fee_tx,
    export_unknown
)
from staketaxcsv.algo.transaction import (
    get_transaction_note,
    get_transfer_sender,
    is_algo_transfer,
    is_app_call,
    is_app_clear,
    is_app_optin,
    is_asset_optin,
    is_transaction_sender,
    is_transfer,
    is_transfer_participant,
    is_transfer_receiver
)


def is_governance_reward_transaction(wallet_address, group):
    if len(group) != 1:
        return False

    transaction = group[0]
    if not is_algo_transfer(transaction):
        return False

    if not is_transfer_receiver(wallet_address, transaction):
        return False

    sender = get_transfer_sender(transaction)
    return sender in co.ADDRESS_GOVERNANCE_REWARDS_POOLS


def handle_governance_reward_transaction(group, exporter, txinfo):
    transaction = group[0]
    payment_details = transaction[co.TRANSACTION_KEY_PAYMENT]

    txinfo.txid = transaction["id"]
    reward = Algo(payment_details["amount"] + transaction["receiver-rewards"])
    export_reward_tx(exporter, txinfo, reward, comment="Governance")


def handle_transfer_transaction(wallet_address, transaction, exporter, txinfo, z_index=0):
    txtype = transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_PAYMENT:
        handle_payment_transaction(wallet_address, transaction, exporter, txinfo, z_index)
    elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
        handle_asa_transaction(wallet_address, transaction, exporter, txinfo, z_index)
    else:
        export_unknown(exporter, txinfo, z_index)


def handle_payment_transaction(wallet_address, transaction, exporter, txinfo, z_index=0):
    payment_details = transaction[co.TRANSACTION_KEY_PAYMENT]
    asset_id = 0

    _handle_transfer(wallet_address, transaction, payment_details, exporter, txinfo, asset_id, z_index)


def handle_asa_transaction(wallet_address, transaction, exporter, txinfo, z_index=0):
    transfer_details = transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
    asset_id = transfer_details["asset-id"]

    _handle_transfer(wallet_address, transaction, transfer_details, exporter, txinfo, asset_id, z_index)


def handle_sender_transaction(transaction, exporter, txinfo, z_index=0):
    fee_amount = transaction["fee"]
    if fee_amount > 0:
        fee = Algo(fee_amount)
        comment = ""
        if is_app_optin(transaction):
            app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
            comment = f"App {app_id} opt-in"
        elif is_app_clear(transaction):
            app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
            comment = f"App {app_id} opt-out"
        export_spend_fee_tx(exporter, txinfo, fee, comment, z_index)

    reward = Algo(transaction["sender-rewards"])
    export_participation_rewards(reward, exporter, txinfo)


def handle_transfer_transactions(wallet_address, transactions, exporter, txinfo, z_index=0):
    num_transfers = 0
    for transaction in transactions:
        if (is_transfer(transaction)
                and not is_asset_optin(transaction)
                and is_transfer_participant(wallet_address, transaction)):
            handle_transfer_transaction(
                wallet_address, transaction, exporter, txinfo, z_index + num_transfers)
            num_transfers += 1
        elif is_app_call(transaction) and "inner-txns" in transaction:
            inner_transactions = transaction.get("inner-txns", [])
            num_transfers += handle_transfer_transactions(
                wallet_address, inner_transactions, exporter, txinfo, z_index + num_transfers)
        elif is_transaction_sender(wallet_address, transaction):
            handle_sender_transaction(transaction, exporter, txinfo, z_index + num_transfers)
    return num_transfers


def _handle_transfer(wallet_address, transaction, details, exporter, txinfo, asset_id, z_index=0):
    txsender = transaction["sender"]
    txreceiver = details["receiver"]
    close_to = details.get("close-to", details.get("close-remainder-to", None))
    rewards_amount = 0

    if wallet_address not in [txsender, txreceiver, close_to]:
        return export_unknown(exporter, txinfo, z_index)

    note = get_transaction_note(transaction)
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
            if txsender == co.ADDRESS_ALGOSTAKE_ESCROW:
                export_reward_tx(exporter, txinfo, receive_asset, fee_amount, "Algostake", z_index)
            elif txsender == co.ADDRESS_PACT_REWARDS:
                export_reward_tx(exporter, txinfo, receive_asset, fee_amount, "Pact", z_index)
            elif txsender in co.ADDRESS_GOVERNANCE_REWARDS_POOLS:
                export_reward_tx(exporter, txinfo, receive_asset, fee_amount, "Governance")
            else:
                if "tinymanStaking/v1" in note:
                    export_reward_tx(exporter, txinfo, receive_asset, fee_amount, "Tinyman", z_index)
                elif txsender == co.ADDRESS_FOLKS_REWARDS and note == "Folks Finance fStaking rewards":
                    export_reward_tx(exporter, txinfo, receive_asset, fee_amount, "Folks Finance", z_index)
                else:
                    export_receive_tx(
                        exporter, txinfo, receive_asset, fee_amount,
                        "Algomint" if txsender == co.ADDRESS_ALGOMINT else note, z_index)
        elif fee_amount > 0:
            fee = Algo(fee_amount)
            export_spend_fee_tx(exporter, txinfo, fee)
    else:
        rewards_amount += transaction["sender-rewards"]
        if close_to and txreceiver != close_to:
            # We are closing the account, but sending the remaining balance is sent to different address
            close_asset = Asset(asset_id, details["close-amount"])
            export_send_tx(exporter, txinfo, close_asset, z_index=z_index)

            send_asset = Asset(asset_id, details["amount"])
            export_send_tx(exporter, txinfo, send_asset, transaction["fee"], txreceiver, z_index=z_index + 1)
        else:
            # Regular send or closing to the same account
            send_asset = Asset(asset_id, details["amount"] + details["close-amount"])

            if txreceiver == co.ADDRESS_PERA and note == "Pera Swap Fee":
                export_spend_fee_tx(exporter, txinfo, send_asset + transaction["fee"], note)
            export_send_tx(
                exporter, txinfo, send_asset, transaction["fee"], txreceiver,
                "Algomint" if txreceiver == co.ADDRESS_ALGOMINT else note, z_index)

    reward = Algo(rewards_amount)
    export_participation_rewards(reward, exporter, txinfo)
