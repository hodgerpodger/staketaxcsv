from algo import constants as co
from algo.asset import Algo, Asset
from algo.handle_unknown import handle_unknown
from common.ExporterTypes import TX_TYPE_LP_DEPOSIT, TX_TYPE_LP_WITHDRAW
from common.make_tx import _make_tx_exchange, make_income_tx, make_just_fee_tx, make_reward_tx, make_swap_tx


def is_tinyman_transaction(group):
    length = len(group)
    if length < 3 or length > 5:
        return False

    if group[1]["tx-type"] != "appl":
        return False

    app_id = group[1]["application-transaction"]["application-id"]
    if (app_id != co.APPLICATION_ID_TINYMAN_v10 and app_id != co.APPLICATION_ID_TINYMAN_v11):
        return False

    return True


def handle_tinyman_transaction(group, exporter, txinfo):
    appl_args = group[1]["application-transaction"]["application-args"]
    if co.TINYMAN_TRANSACTION_SWAP in appl_args:
        _handle_tinyman_swap(group, exporter, txinfo)
    elif co.TINYMAN_TRANSACTION_REDEEM in appl_args:
        _handle_tinyman_redeem(group, exporter, txinfo)
    elif co.TINYMAN_TRANSACTION_LP_ADD in appl_args:
        _handle_tinyman_lp_add(group, exporter, txinfo)
    elif co.TINYMAN_TRANSACTION_LP_REMOVE in appl_args:
        _handle_tinyman_lp_remove(group, exporter, txinfo)
    else:
        handle_unknown(exporter, txinfo)


def _handle_tinyman_swap(group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction["payment-transaction"]["amount"] + fee_transaction["fee"]

    reward = Algo(fee_transaction["sender-rewards"])
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)

    appl_transaction = group[1]
    fee_amount += appl_transaction["fee"]

    send_transaction = group[2]
    fee_amount += send_transaction["fee"]
    send_asset = _get_transfer_asset(send_transaction)
    # https://docs.tinyman.org/fees
    swap_fee = send_asset * 0.003
    send_asset -= swap_fee
    row = make_just_fee_tx(txinfo, swap_fee.amount, swap_fee.ticker)
    exporter.ingest_row(row)

    receive_transaction = group[3]
    fee_amount += receive_transaction["fee"]
    receive_asset = _get_transfer_asset(receive_transaction)

    fee = Algo(fee_amount)
    txinfo.fee = fee.amount
    txinfo.comment = "Tinyman"

    row = make_swap_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    exporter.ingest_row(row)


def _get_transfer_asset(transaction):
    amount = 0
    asset_id = 0
    txtype = transaction["tx-type"]
    if txtype == "pay":
        amount = transaction["payment-transaction"]["amount"]
    elif txtype == "axfer":
        amount = transaction["asset-transfer-transaction"]["amount"]
        asset_id = transaction["asset-transfer-transaction"]["asset-id"]

    return Asset(asset_id, amount)


def _handle_tinyman_redeem(group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction["payment-transaction"]["amount"] + fee_transaction["fee"]

    reward = Algo(fee_transaction["sender-rewards"])
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)

    appl_transaction = group[1]
    fee_amount += appl_transaction["fee"]

    receive_transaction = group[2]
    fee_amount += receive_transaction["fee"]
    receive_asset = _get_transfer_asset(receive_transaction)

    fee = Algo(fee_amount)
    txinfo.fee = fee.amount
    txinfo.comment = "Tinyman"

    row = make_income_tx(txinfo, receive_asset.amount, receive_asset.ticker)
    exporter.ingest_row(row)


def _handle_tinyman_lp_add(group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction["payment-transaction"]["amount"] + fee_transaction["fee"]

    reward = Algo(fee_transaction["sender-rewards"])
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)

    appl_transaction = group[1]
    fee_amount += appl_transaction["fee"]

    send_transaction = group[2]
    fee_amount += send_transaction["fee"]
    send_asset_1 = _get_transfer_asset(send_transaction)

    send_transaction = group[3]
    fee_amount += send_transaction["fee"]
    send_asset_2 = _get_transfer_asset(send_transaction)

    receive_transaction = group[4]
    fee_amount += receive_transaction["fee"]
    lp_asset = _get_transfer_asset(receive_transaction)

    fee = Algo(fee_amount / 2)
    txinfo.fee = fee.amount
    txinfo.comment = "Tinyman"

    row = _make_tx_exchange(
        txinfo, send_asset_1.amount, send_asset_1.ticker,
        lp_asset.amount / 2, lp_asset.ticker, TX_TYPE_LP_DEPOSIT)
    exporter.ingest_row(row)

    row = _make_tx_exchange(
        txinfo, send_asset_2.amount, send_asset_2.ticker,
        lp_asset.amount / 2, lp_asset.ticker, TX_TYPE_LP_DEPOSIT)
    exporter.ingest_row(row)


def _handle_tinyman_lp_remove(group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction["payment-transaction"]["amount"] + fee_transaction["fee"]

    reward = Algo(fee_transaction["sender-rewards"])
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)

    appl_transaction = group[1]
    fee_amount += appl_transaction["fee"]

    receive_transaction = group[2]
    fee_amount += receive_transaction["fee"]
    receive_asset_1 = _get_transfer_asset(receive_transaction)

    receive_transaction = group[3]
    fee_amount += receive_transaction["fee"]
    receive_asset_2 = _get_transfer_asset(receive_transaction)

    send_transaction = group[4]
    fee_amount += receive_transaction["fee"]
    lp_asset = _get_transfer_asset(send_transaction)

    fee = Algo(fee_amount / 2)
    txinfo.fee = fee.amount
    txinfo.comment = "Tinyman"

    row = _make_tx_exchange(
        txinfo, lp_asset.amount / 2, lp_asset.ticker,
        receive_asset_1.amount, receive_asset_1.ticker,
        TX_TYPE_LP_WITHDRAW)
    exporter.ingest_row(row)

    row = _make_tx_exchange(
        txinfo, lp_asset.amount / 2, lp_asset.ticker,
        receive_asset_2.amount, receive_asset_2.ticker,
        TX_TYPE_LP_WITHDRAW)
    exporter.ingest_row(row)
