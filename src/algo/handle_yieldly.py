from algo import constants as co
from algo.asset import Algo, Asset
from algo.handle_simple import handle_participation_rewards
from algo.util_algo import get_transfer_asset
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
APPLICATION_ID_YIELDLY_YLDY_RIO_POOL = 604219363
APPLICATION_ID_YIELDLY_YLDY_AO_POOL = 604373501
APPLICATION_ID_YIELDLY_YLDY_CHIP_POOL = 604392265
APPLICATION_ID_YIELDLY_YLDY_FLAMINGO_POOL = 604411076
APPLICATION_ID_YIELDLY_YLDY_WBLN_POOL = 609492331
APPLICATION_ID_YIELDLY_YLDY_BIRDS_POOL = 604434381
APPLICATION_ID_YIELDLY_YLDY_DPANDA_POOL = 617707129
APPLICATION_ID_YIELDLY_YLDY_CURATOR_POOL = 618390867
APPLICATION_ID_YIELDLY_YLDY_ACORN_POOL = 620458102
APPLICATION_ID_YIELDLY_YLDY_CRSD_POOL = 624919018
APPLICATION_ID_YIELDLY_YLDY_NURD_POOL = 625053603
APPLICATION_ID_YIELDLY_YLDY_NEKOS_POOL = 620625200
APPLICATION_ID_YIELDLY_AKITA_LP_POOL = 511593477
APPLICATION_ID_YIELDLY_AKTA_LP_POOL = 556355279
APPLICATION_ID_YIELDLY_XET_LP_POOL = 568949192
APPLICATION_ID_YIELDLY_ARCC_LP_POOL = 583355704
APPLICATION_ID_YIELDLY_DEFLY_LP_POOL = 591416743
APPLICATION_ID_YIELDLY_KTNC_LP_POOL = 593133882
APPLICATION_ID_YIELDLY_TINY_LP_POOL = 593278929
APPLICATION_ID_YIELDLY_TREES_LP_POOL = 593294372
APPLICATION_ID_YIELDLY_HDL_LP_POOL = 596954871
APPLICATION_ID_YIELDLY_BLOCK_LP_POOL = 593337625
APPLICATION_ID_YIELDLY_RIO_LP_POOL = 604223245
APPLICATION_ID_YIELDLY_AO_LP_POOL = 604375580
APPLICATION_ID_YIELDLY_CHIP_LP_POOL = 604393901
APPLICATION_ID_YIELDLY_FLAMINGO_LP_POOL = 604412989
APPLICATION_ID_YIELDLY_WBLN_LP_POOL = 609496314
APPLICATION_ID_YIELDLY_BIRDS_LP_POOL = 604437391
APPLICATION_ID_YIELDLY_DPANDA_LP_POOL = 617728717
APPLICATION_ID_YIELDLY_CURATOR_LP_POOL = 618393134
APPLICATION_ID_YIELDLY_ACORN_LP_POOL = 620461252
APPLICATION_ID_YIELDLY_CRSD_LP_POOL = 620601402
APPLICATION_ID_YIELDLY_NURD_LP_POOL = 625087406
APPLICATION_ID_YIELDLY_NEKOS_LP_POOL = 620627151

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
    APPLICATION_ID_YIELDLY_YLDY_RIO_POOL,
    APPLICATION_ID_YIELDLY_YLDY_AO_POOL,
    APPLICATION_ID_YIELDLY_YLDY_CHIP_POOL,
    APPLICATION_ID_YIELDLY_YLDY_FLAMINGO_POOL,
    APPLICATION_ID_YIELDLY_YLDY_WBLN_POOL,
    APPLICATION_ID_YIELDLY_YLDY_BIRDS_POOL,
    APPLICATION_ID_YIELDLY_YLDY_DPANDA_POOL,
    APPLICATION_ID_YIELDLY_YLDY_CURATOR_POOL,
    APPLICATION_ID_YIELDLY_YLDY_ACORN_POOL,
    APPLICATION_ID_YIELDLY_YLDY_CRSD_POOL,
    APPLICATION_ID_YIELDLY_YLDY_NURD_POOL,
    APPLICATION_ID_YIELDLY_YLDY_NEKOS_POOL,
    APPLICATION_ID_YIELDLY_AKITA_LP_POOL,
    APPLICATION_ID_YIELDLY_AKTA_LP_POOL,
    APPLICATION_ID_YIELDLY_XET_LP_POOL,
    APPLICATION_ID_YIELDLY_ARCC_LP_POOL,
    APPLICATION_ID_YIELDLY_DEFLY_LP_POOL,
    APPLICATION_ID_YIELDLY_KTNC_LP_POOL,
    APPLICATION_ID_YIELDLY_TINY_LP_POOL,
    APPLICATION_ID_YIELDLY_TREES_LP_POOL,
    APPLICATION_ID_YIELDLY_HDL_LP_POOL,
    APPLICATION_ID_YIELDLY_BLOCK_LP_POOL,
    APPLICATION_ID_YIELDLY_RIO_LP_POOL,
    APPLICATION_ID_YIELDLY_AO_LP_POOL,
    APPLICATION_ID_YIELDLY_CHIP_LP_POOL,
    APPLICATION_ID_YIELDLY_FLAMINGO_LP_POOL,
    APPLICATION_ID_YIELDLY_WBLN_LP_POOL,
    APPLICATION_ID_YIELDLY_BIRDS_LP_POOL,
    APPLICATION_ID_YIELDLY_DPANDA_LP_POOL,
    APPLICATION_ID_YIELDLY_CURATOR_LP_POOL,
    APPLICATION_ID_YIELDLY_ACORN_LP_POOL,
    APPLICATION_ID_YIELDLY_CRSD_LP_POOL,
    APPLICATION_ID_YIELDLY_NURD_LP_POOL,
    APPLICATION_ID_YIELDLY_NEKOS_LP_POOL
]

YIELDLY_TRANSACTION_POOL_CLAIM = "Q0E="         # "CA"
YIELDLY_TRANSACTION_POOL_CLOSE = "Q0FX"         # "CAW"
YIELDLY_TRANSACTION_POOL_BAIL = "YmFpbA=="      # "bail"
YIELDLY_TRANSACTION_POOL_CLAIM_T5 = "Y2xhaW0="  # "claim"


def is_yieldly_transaction(group):
    length = len(group)
    if length < 2 or length > 6:
        return False

    if group[0]["tx-type"] != "appl":
        return False

    if group[1]["tx-type"] == "appl":
        app_id = group[1][co.TRANSACTION_KEY_APP_CALL]["application-id"]
    else:
        app_id = group[0][co.TRANSACTION_KEY_APP_CALL]["application-id"]

    return app_id in YIELDLY_APPLICATIONS


def handle_yieldly_transaction(group, exporter, txinfo):
    init_transaction = group[0]
    reward = Algo(init_transaction["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    app_transaction = group[1]
    txtype = app_transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_APP_CALL:
        app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if YIELDLY_TRANSACTION_POOL_CLAIM in appl_args:
            if app_id == APPLICATION_ID_YIELDLY_NLL:
                _handle_yieldly_nll(group, exporter, txinfo)
            elif app_id == APPLICATION_ID_YIELDLY_YLDY_ALGO_POOL:
                _handle_yieldly_algo_pool_claim(group, exporter, txinfo)
            elif app_id in YIELDLY_APPLICATIONS:
                _handle_yieldly_asa_pool_claim(group, exporter, txinfo)
        elif YIELDLY_TRANSACTION_POOL_CLOSE in appl_args:
            # Claims and legacy closeouts are handled the same way
            _handle_yieldly_asa_pool_claim(group, exporter, txinfo)
        elif YIELDLY_TRANSACTION_POOL_BAIL in appl_args:
            app_transaction = group[0]
            appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
            if (app_transaction[co.TRANSACTION_KEY_APP_CALL]["on-completion"] == "closeout"
                    and "inner-txns" in app_transaction
                    and len(app_transaction["inner-txns"]) == 2):
                _handle_yieldly_asa_pool_close(group, exporter, txinfo)
            elif YIELDLY_TRANSACTION_POOL_CLAIM_T5 in appl_args:
                _handle_yieldly_teal5_pool_claim(group, exporter, txinfo)
    else:
        # Ignore stake transactions
        pass


def _handle_yieldly_nll(group, exporter, txinfo):
    init_transaction = group[0]
    app_transaction = group[1]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    asset_transaction = group[2]
    transfer_details = asset_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
    reward = Asset(transfer_details["asset-id"], transfer_details["amount"])

    fee_transaction = group[3]
    fee_amount += fee_transaction["fee"] + fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"]

    fee = Algo(fee_amount)
    txinfo.comment = "Yieldly NLL"

    row = make_reward_tx(txinfo, reward, reward.ticker)
    row.fee = fee.amount
    exporter.ingest_row(row)


def _handle_yieldly_algo_pool_claim(group, exporter, txinfo):
    init_transaction = group[0]
    app_transaction = group[1]
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

    # Distribute fee over the two transactions
    fee = Algo(fee_amount / 2)
    txinfo.comment = "Yieldly Staking Pool"

    row = make_reward_tx(txinfo, yldy_reward, yldy_reward.ticker)
    row.fee = fee.amount
    exporter.ingest_row(row)

    row = make_reward_tx(txinfo, algo_reward, algo_reward.ticker)
    row.fee = fee.amount
    exporter.ingest_row(row)


def _handle_yieldly_asa_pool_claim(group, exporter, txinfo):
    init_transaction = group[0]
    app_transaction = group[1]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    asset_transaction = group[2]
    transfer_details = asset_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
    reward = Asset(transfer_details["asset-id"], transfer_details["amount"])

    if not reward.zero():
        fee = Algo(fee_amount)
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if YIELDLY_TRANSACTION_POOL_CLOSE in appl_args:
            txinfo.comment = "Yieldly Staking Pool Close"
        else:
            txinfo.comment = "Yieldly Staking Pool"

        row = make_reward_tx(txinfo, reward, reward.ticker)
        row.fee = fee.amount
        exporter.ingest_row(row)


def _handle_yieldly_asa_pool_close(group, exporter, txinfo):
    app_transaction = group[0]
    app_bail_transaction = group[1]
    fee_amount = app_bail_transaction["fee"] + app_transaction["fee"]

    # First inner transaction is a deposit withdraw
    # Second inner transaction is pending rewards claim
    asset_transaction = app_transaction["inner-txns"][1]
    transfer_details = asset_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]
    reward = Asset(transfer_details["asset-id"], transfer_details["amount"])

    if not reward.zero():
        fee = Algo(fee_amount)
        txinfo.comment = "Yieldly Staking Pool Close"

        row = make_reward_tx(txinfo, reward, reward.ticker)
        row.fee = fee.amount
        exporter.ingest_row(row)


def _handle_yieldly_teal5_pool_claim(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[0]
    inner_transactions = app_transaction.get("inner-txns", [])
    length = len(inner_transactions)
    if length > 0:
        fee = Algo(fee_amount / length)
        txinfo.comment = "Yieldly Staking Pool"

        for transaction in inner_transactions:
            reward = get_transfer_asset(transaction)
            if not reward.zero():
                row = make_reward_tx(txinfo, reward, reward.ticker)
                row.fee = fee.amount
                exporter.ingest_row(row)
