from algo import constants as co
from algo.asset import Algo, Asset
from common.make_tx import make_reward_tx


def is_yieldly_transaction(group):
    length = len(group)
    if length < 3 or length > 6:
        return False

    if (group[0]["tx-type"] != "appl" or group[1]["tx-type"] != "appl"):
        return False

    app_id = group[1]["application-transaction"]["application-id"]
    if app_id not in co.YIELDLY_APPLICATIONS:
        return False

    return True


def handle_yieldly_transaction(group, exporter, txinfo):
    init_transaction = group[0]
    reward = Algo(init_transaction["sender-rewards"])
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)

    app_id = group[1]["application-transaction"]["application-id"]
    if app_id == co.APPLICATION_ID_YIELDLY_NLL:
        _handle_yieldly_nll(group, exporter, txinfo)
    elif app_id == co.APPLICATION_ID_YIELDLY_YLDY_ALGO_POOL:
        _handle_yieldly_algo_pool_claim(group, exporter, txinfo)
    elif app_id in co.YIELDLY_APPLICATIONS:
        _handle_yieldly_asa_pool_claim(group, exporter, txinfo)


def _handle_yieldly_nll(group, exporter, txinfo):
    app_transaction = group[1]
    appl_args = app_transaction["application-transaction"]["application-args"]
    if co.YIELDLY_TRANSACTION_POOL_CLAIM not in appl_args:
        return
    init_transaction = group[0]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    asset_transaction = group[2]
    transfer_details = asset_transaction["asset-transfer-transaction"]
    reward = Asset(transfer_details["asset-id"], transfer_details["amount"])
    fee_amount += asset_transaction["fee"]

    fee_transaction = group[3]
    fee_amount = fee_transaction["fee"] + fee_transaction["payment-transaction"]["amount"]

    fee = Algo(fee_amount)
    txinfo.fee = fee.amount
    txinfo.comment = "Yieldly NLL"

    row = make_reward_tx(txinfo, reward, reward.ticker)
    exporter.ingest_row(row)


def _handle_yieldly_algo_pool_claim(group, exporter, txinfo):
    app_transaction = group[1]
    appl_args = app_transaction["application-transaction"]["application-args"]
    if co.YIELDLY_TRANSACTION_POOL_CLAIM not in appl_args:
        return
    init_transaction = group[0]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    app_transaction = group[2]
    fee_amount += app_transaction["fee"]

    axfer_transaction = group[3]
    transfer_details = axfer_transaction["asset-transfer-transaction"]
    yldy_reward = Asset(transfer_details["asset-id"], transfer_details["amount"])
    fee_amount += axfer_transaction["fee"]

    pay_transaction = group[4]
    transfer_details = pay_transaction["payment-transaction"]
    algo_reward = Algo(transfer_details["amount"])
    fee_amount += pay_transaction["fee"]

    fee_transaction = group[5]
    fee_amount = fee_transaction["fee"] + fee_transaction["payment-transaction"]["amount"]

    fee = Algo(fee_amount / 2)
    txinfo.fee = fee.amount
    txinfo.comment = "Yieldly Staking Pool"

    row = make_reward_tx(txinfo, yldy_reward, yldy_reward.ticker)
    exporter.ingest_row(row)

    row = make_reward_tx(txinfo, algo_reward, algo_reward.ticker)
    exporter.ingest_row(row)


def _handle_yieldly_asa_pool_claim(group, exporter, txinfo):
    app_transaction = group[1]
    appl_args = app_transaction["application-transaction"]["application-args"]
    is_pool_claim = co.YIELDLY_TRANSACTION_POOL_CLAIM in appl_args
    is_pool_close = co.YIELDLY_TRANSACTION_POOL_CLOSE in appl_args
    if (not is_pool_claim and not is_pool_close):
        return
    global_state = app_transaction["global-state-delta"]
    has_pending_claim = any(item for item in global_state if item["key"] == co.YIELDLY_TRANSACTION_POOL_CLAIM)
    if (is_pool_close and not has_pending_claim):
        return
    init_transaction = group[0]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    asset_transaction = group[2]
    transfer_details = asset_transaction["asset-transfer-transaction"]
    reward = Asset(transfer_details["asset-id"], transfer_details["amount"])
    fee_amount += asset_transaction["fee"]

    fee = Algo(fee_amount)
    txinfo.fee = fee.amount
    txinfo.comment = "Yieldly Staking Pool"

    row = make_reward_tx(txinfo, reward, reward.ticker)
    exporter.ingest_row(row)
    return
