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


def handle_payment_transaction(wallet_address, elem, exporter, txinfo):
    payment_details = elem["payment-transaction"]
    txsender = elem["sender"]
    txreceiver = payment_details["receiver"]
    amount = Algo(payment_details["amount"])

    _handle_transfer(wallet_address, elem, exporter, txinfo, amount, txsender, txreceiver)

    # When closing an account the remaining balance is transferred to "close-remainder-to"
    if "close-remainder-to" in payment_details:
        txreceiver = payment_details["close-remainder-to"]
        amount = Algo(payment_details["close-amount"])
        if not amount.zero():
            row = make_transfer_out_tx(txinfo, amount, amount.ticker, txreceiver)
            exporter.ingest_row(row)


def handle_asa_transaction(wallet_address, elem, exporter, txinfo):
    transfer_details = elem["asset-transfer-transaction"]
    txsender = elem["sender"]
    txreceiver = transfer_details["receiver"]
    asset_id = transfer_details["asset-id"]
    amount = Asset(asset_id, transfer_details["amount"])

    _handle_transfer(wallet_address, elem, exporter, txinfo, amount, txsender, txreceiver)

    if "close-to" in transfer_details:
        txreceiver = transfer_details["close-to"]
        amount = Asset(asset_id, transfer_details["close-amount"])
        if not amount.zero():
            row = make_transfer_out_tx(txinfo, amount, amount.ticker, txreceiver)
            exporter.ingest_row(row)


def _handle_transfer(wallet_address, elem, exporter, txinfo, amount, txsender, txreceiver):
    if not amount.zero():
        row = None
        if wallet_address == txsender:
            row = make_transfer_out_tx(txinfo, amount, amount.ticker, txreceiver)
        else:
            row = make_transfer_in_tx(txinfo, amount, amount.ticker)
        exporter.ingest_row(row)
        # Fee already paid
        txinfo.fee = 0

    reward = Algo(max(elem["sender-rewards"], elem["receiver-rewards"]))
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)
