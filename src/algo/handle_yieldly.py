from algo import constants as co
from algo.asset import Algo, Asset
from common.make_tx import make_reward_tx

APPLICATION_ID_YIELDLY = 233725848
APPLICATION_ID_YIELDLY_NLL = 233725844
APPLICATION_ID_YIELDLY_YLDY_ALGO_POOL = 233725850
APPLICATION_ID_YIELDLY_YLDY_OPUL_POOL = 348079765
APPLICATION_ID_YIELDLY_OPUL_OPUL_POOL = 367431051
APPLICATION_ID_YIELDLY_YLDY_SMILE_POOL = 352116819
APPLICATION_ID_YIELDLY_SMILE_SMILE_POOL = 373819681
APPLICATION_ID_YIELDLY_YLDY_ARCC_POOL = 385089192
APPLICATION_ID_YIELDLY_ARRC_ARCC_POOL = 498747685
APPLICATION_ID_YIELDLY_YLDY_GEMS_POOL = 393388133
APPLICATION_ID_YIELDLY_GEMS_GEMS_POOL = 419301793
APPLICATION_ID_YIELDLY_YLDY_XET_POOL = 424101057
APPLICATION_ID_YIELDLY_XET_XET_POOL = 470390215
APPLICATION_ID_YIELDLY_YLDY_CHOICE_POOL = 447336112
APPLICATION_ID_YIELDLY_CHOICE_CHOICE_POOL = 464365150
APPLICATION_ID_YIELDLY_YLDY_AKITA_POOL = 511597182
APPLICATION_ID_YIELDLY_YLDY_ARCC_T5_POOL = 583357499
APPLICATION_ID_YIELDLY_YLDY_DEFLY_POOL = 591414576
APPLICATION_ID_YIELDLY_YLDY_KTNC_POOL = 593126242
APPLICATION_ID_YIELDLY_YLDY_TINY_POOL = 593270704
APPLICATION_ID_YIELDLY_YLDY_TREES_POOL = 593289960
APPLICATION_ID_YIELDLY_YLDY_HDL_POOL = 596950925
APPLICATION_ID_YIELDLY_YLDY_BLOCK_POOL = 593324268
APPLICATION_ID_YIELDLY_AKITA_LP_POOL = 511593477
APPLICATION_ID_YIELDLY_XET_LP_POOL = 568949192
APPLICATION_ID_YIELDLY_ARCC_LP_POOL = 583355704
APPLICATION_ID_YIELDLY_DEFLY_LP_POOL = 591416743
APPLICATION_ID_YIELDLY_KTNC_LP_POOL = 593133882
APPLICATION_ID_YIELDLY_TINY_LP_POOL = 593278929
APPLICATION_ID_YIELDLY_TREES_LP_POOL = 593294372
APPLICATION_ID_YIELDLY_HDL_LP_POOL = 596954871
APPLICATION_ID_YIELDLY_BLOCK_LP_POOL = 593337625

YIELDLY_APPLICATIONS = [
    APPLICATION_ID_YIELDLY,
    APPLICATION_ID_YIELDLY_NLL,
    APPLICATION_ID_YIELDLY_YLDY_ALGO_POOL,
    APPLICATION_ID_YIELDLY_YLDY_OPUL_POOL,
    APPLICATION_ID_YIELDLY_OPUL_OPUL_POOL,
    APPLICATION_ID_YIELDLY_YLDY_SMILE_POOL,
    APPLICATION_ID_YIELDLY_SMILE_SMILE_POOL,
    APPLICATION_ID_YIELDLY_YLDY_ARCC_POOL,
    APPLICATION_ID_YIELDLY_ARRC_ARCC_POOL,
    APPLICATION_ID_YIELDLY_YLDY_GEMS_POOL,
    APPLICATION_ID_YIELDLY_GEMS_GEMS_POOL,
    APPLICATION_ID_YIELDLY_YLDY_XET_POOL,
    APPLICATION_ID_YIELDLY_XET_XET_POOL,
    APPLICATION_ID_YIELDLY_YLDY_CHOICE_POOL,
    APPLICATION_ID_YIELDLY_CHOICE_CHOICE_POOL,
    APPLICATION_ID_YIELDLY_YLDY_AKITA_POOL,
    APPLICATION_ID_YIELDLY_YLDY_ARCC_T5_POOL,
    APPLICATION_ID_YIELDLY_YLDY_DEFLY_POOL,
    APPLICATION_ID_YIELDLY_YLDY_KTNC_POOL,
    APPLICATION_ID_YIELDLY_YLDY_TINY_POOL,
    APPLICATION_ID_YIELDLY_YLDY_TREES_POOL,
    APPLICATION_ID_YIELDLY_YLDY_HDL_POOL,
    APPLICATION_ID_YIELDLY_YLDY_BLOCK_POOL,
    APPLICATION_ID_YIELDLY_AKITA_LP_POOL,
    APPLICATION_ID_YIELDLY_XET_LP_POOL,
    APPLICATION_ID_YIELDLY_ARCC_LP_POOL,
    APPLICATION_ID_YIELDLY_DEFLY_LP_POOL,
    APPLICATION_ID_YIELDLY_KTNC_LP_POOL,
    APPLICATION_ID_YIELDLY_TINY_LP_POOL,
    APPLICATION_ID_YIELDLY_TREES_LP_POOL,
    APPLICATION_ID_YIELDLY_HDL_LP_POOL,
    APPLICATION_ID_YIELDLY_BLOCK_LP_POOL,
]

YIELDLY_TRANSACTION_POOL_CLAIM = "Q0E="
YIELDLY_TRANSACTION_POOL_CLOSE = "Q0FX"


def is_yieldly_transaction(group):
    length = len(group)
    if length < 3 or length > 6:
        return False

    if (group[0]["tx-type"] != "appl" or group[1]["tx-type"] != "appl"):
        return False

    app_id = group[1][co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id not in YIELDLY_APPLICATIONS:
        return False

    return True


def handle_yieldly_transaction(group, exporter, txinfo):
    init_transaction = group[0]
    reward = Algo(init_transaction["sender-rewards"])
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)

    app_id = group[1][co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id == APPLICATION_ID_YIELDLY_NLL:
        _handle_yieldly_nll(group, exporter, txinfo)
    elif app_id == APPLICATION_ID_YIELDLY_YLDY_ALGO_POOL:
        _handle_yieldly_algo_pool_claim(group, exporter, txinfo)
    elif app_id in YIELDLY_APPLICATIONS:
        _handle_yieldly_asa_pool_claim(group, exporter, txinfo)


def _handle_yieldly_nll(group, exporter, txinfo):
    app_transaction = group[1]
    appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if YIELDLY_TRANSACTION_POOL_CLAIM not in appl_args:
        return
    init_transaction = group[0]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    asset_transaction = group[2]
    transfer_details = asset_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
    reward = Asset(transfer_details["asset-id"], transfer_details["amount"])

    fee_transaction = group[3]
    fee_amount += fee_transaction["fee"] + fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"]

    fee = Algo(fee_amount)
    txinfo.fee = fee.amount
    txinfo.comment = "Yieldly NLL"

    row = make_reward_tx(txinfo, reward, reward.ticker)
    exporter.ingest_row(row)


def _handle_yieldly_algo_pool_claim(group, exporter, txinfo):
    app_transaction = group[1]
    appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if YIELDLY_TRANSACTION_POOL_CLAIM not in appl_args:
        return
    init_transaction = group[0]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    app_transaction = group[2]
    fee_amount += app_transaction["fee"]

    axfer_transaction = group[3]
    transfer_details = axfer_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
    yldy_reward = Asset(transfer_details["asset-id"], transfer_details["amount"])

    pay_transaction = group[4]
    transfer_details = pay_transaction[co.TRANSACTION_KEY_PAYMENT]
    algo_reward = Algo(transfer_details["amount"])

    fee_transaction = group[5]
    fee_amount = fee_transaction["fee"] + fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"]

    fee = Algo(fee_amount / 2)
    txinfo.fee = fee.amount
    txinfo.comment = "Yieldly Staking Pool"

    row = make_reward_tx(txinfo, yldy_reward, yldy_reward.ticker)
    exporter.ingest_row(row)

    row = make_reward_tx(txinfo, algo_reward, algo_reward.ticker)
    exporter.ingest_row(row)


def _handle_yieldly_asa_pool_claim(group, exporter, txinfo):
    app_transaction = group[1]
    appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    is_pool_claim = YIELDLY_TRANSACTION_POOL_CLAIM in appl_args
    is_pool_close = YIELDLY_TRANSACTION_POOL_CLOSE in appl_args
    if (not is_pool_claim and not is_pool_close):
        return
    global_state = app_transaction["global-state-delta"]
    has_pending_claim = any(item for item in global_state if item["key"] == YIELDLY_TRANSACTION_POOL_CLAIM)
    if (is_pool_close and not has_pending_claim):
        return
    init_transaction = group[0]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    asset_transaction = group[2]
    transfer_details = asset_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
    reward = Asset(transfer_details["asset-id"], transfer_details["amount"])

    fee = Algo(fee_amount)
    txinfo.fee = fee.amount
    txinfo.comment = "Yieldly Staking Pool"

    row = make_reward_tx(txinfo, reward, reward.ticker)
    exporter.ingest_row(row)
    return
