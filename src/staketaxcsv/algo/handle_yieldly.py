from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import export_reward_tx, export_stake_tx, export_unstake_tx
from staketaxcsv.algo.handle_simple import handle_participation_rewards, handle_unknown
from staketaxcsv.algo.transaction import get_inner_transfer_asset, get_transfer_asset

APPLICATION_ID_YIELDLY = 233725848
APPLICATION_ID_YIELDLY_NLL = 233725844

APPLICATION_ID_YIELDLY_YLDY_ALGO_POOL = 233725850

YIELDLY_APPLICATIONS = [
    APPLICATION_ID_YIELDLY,
    APPLICATION_ID_YIELDLY_NLL,
    APPLICATION_ID_YIELDLY_YLDY_ALGO_POOL,

    348079765,  # APPLICATION_ID_YIELDLY_YLDY_OPUL_POOL
    367431051,  # APPLICATION_ID_YIELDLY_OPUL_OPUL_POOL
    352116819,  # APPLICATION_ID_YIELDLY_YLDY_SMILE_POOL
    373819681,  # APPLICATION_ID_YIELDLY_SMILE_SMILE_POOL
    385089192,  # APPLICATION_ID_YIELDLY_YLDY_ARCC_POOL
    498747685,  # APPLICATION_ID_YIELDLY_ARRC_ARCC_POOL
    393388133,  # APPLICATION_ID_YIELDLY_YLDY_GEMS_POOL
    419301793,  # APPLICATION_ID_YIELDLY_GEMS_GEMS_POOL
    424101057,  # APPLICATION_ID_YIELDLY_YLDY_XET_POOL
    470390215,  # APPLICATION_ID_YIELDLY_XET_XET_POOL
    772221734,  # APPLICATION_ID_YIELDLY_XET_XET_2_POOL
    447336112,  # APPLICATION_ID_YIELDLY_YLDY_CHOICE_POOL
    464365150,  # APPLICATION_ID_YIELDLY_CHOICE_CHOICE_POOL
    725020782,  # APPLICATION_ID_YIELDLY_CHOICE_CHOICE_2_POOL
    511597182,  # APPLICATION_ID_YIELDLY_YLDY_AKITA_POOL
    583357499,  # APPLICATION_ID_YIELDLY_YLDY_ARCC_T5_POOL
    591414576,  # APPLICATION_ID_YIELDLY_YLDY_DEFLY_POOL
    593126242,  # APPLICATION_ID_YIELDLY_YLDY_KTNC_POOL
    593270704,  # APPLICATION_ID_YIELDLY_YLDY_TINY_POOL
    593289960,  # APPLICATION_ID_YIELDLY_YLDY_TREES_POOL
    596950925,  # APPLICATION_ID_YIELDLY_YLDY_HDL_POOL
    593324268,  # APPLICATION_ID_YIELDLY_YLDY_BLOCK_POOL
    604219363,  # APPLICATION_ID_YIELDLY_YLDY_RIO_POOL
    604373501,  # APPLICATION_ID_YIELDLY_YLDY_AO_POOL
    604392265,  # APPLICATION_ID_YIELDLY_YLDY_CHIP_POOL
    604411076,  # APPLICATION_ID_YIELDLY_YLDY_FLAMINGO_POOL
    609492331,  # APPLICATION_ID_YIELDLY_YLDY_WBLN_POOL
    604434381,  # APPLICATION_ID_YIELDLY_YLDY_BIRDS_POOL
    617707129,  # APPLICATION_ID_YIELDLY_YLDY_DPANDA_POOL
    618390867,  # APPLICATION_ID_YIELDLY_YLDY_CURATOR_POOL
    620458102,  # APPLICATION_ID_YIELDLY_YLDY_ACORN_POOL
    624919018,  # APPLICATION_ID_YIELDLY_YLDY_CRSD_POOL
    625053603,  # APPLICATION_ID_YIELDLY_YLDY_NURD_POOL
    708128650,  # APPLICATION_ID_YIELDLY_NURD_NURD_POOL
    620625200,  # APPLICATION_ID_YIELDLY_YLDY_NEKOS_POOL
    710518651,  # APPLICATION_ID_YIELDLY_YLDY_COSG_POOL
    710543830,  # APPLICATION_ID_YIELDLY_COSG_COSG_POOL
    751028283,  # APPLICATION_ID_YIELDLY_COSG_COSG_2_POOL
    828853946,  # APPLICATION_ID_YIELDLY_COSG_COSG_3_POOL
    829174811,  # APPLICATION_ID_YIELDLY_COSG_COSG_4_POOL
    717256390,  # APPLICATION_ID_YIELDLY_YLDY_ALCH_POOL
    751347943,  # APPLICATION_ID_YIELDLY_YLDY_ASASTATS_POOL
    814102655,  # APPLICATION_ID_YIELDLY_YLDY_ASASTATS_2_POOL
    751459877,  # APPLICATION_ID_YIELDLY_ASASTATS_ASASTATS_POOL
    754135308,  # APPLICATION_ID_YIELDLY_YLDY_BOARD_POOL
    835504964,  # APPLICATION_ID_YIELDLY_YLDY_BOARD_2_POOL
    754181252,  # APPLICATION_ID_YIELDLY_BOARD_BOARD_POOL
    779181697,  # APPLICATION_ID_YIELDLY_YLDY_ALGX_POOL
    779198429,  # APPLICATION_ID_YIELDLY_ALGX_ALGX_POOL
    786777082,  # APPLICATION_ID_YIELDLY_YLDY_XGLI_POOL
    792754415,  # APPLICATION_ID_YIELDLY_YLDY_KITSU_POOL
    858089184,  # APPLICATION_ID_YIELDLY_YLDY_KITSU_2_POOL
    864612763,  # APPLICATION_ID_YIELDLY_YLDY_DBD_POOL
    888151708,  # APPLICATION_ID_YIELDLY_YLDY_GARDIAN_POOL

    511593477,  # APPLICATION_ID_YIELDLY_AKITA_LP_POOL
    556355279,  # APPLICATION_ID_YIELDLY_AKTA_LP_POOL
    568949192,  # APPLICATION_ID_YIELDLY_XET_LP_POOL
    772207612,  # APPLICATION_ID_YIELDLY_XET_LP_2_POOL
    583355704,  # APPLICATION_ID_YIELDLY_ARCC_LP_POOL
    591416743,  # APPLICATION_ID_YIELDLY_DEFLY_LP_POOL
    593133882,  # APPLICATION_ID_YIELDLY_KTNC_LP_POOL
    593278929,  # APPLICATION_ID_YIELDLY_TINY_LP_POOL
    593294372,  # APPLICATION_ID_YIELDLY_TREES_LP_POOL
    762480142,  # APPLICATION_ID_YIELDLY_TREES_LP_2_POOL
    596954871,  # APPLICATION_ID_YIELDLY_HDL_LP_POOL
    743316099,  # APPLICATION_ID_YIELDLY_HDL_LP_2_POOL
    593337625,  # APPLICATION_ID_YIELDLY_BLOCK_LP_POOL
    604223245,  # APPLICATION_ID_YIELDLY_RIO_LP_POOL
    604375580,  # APPLICATION_ID_YIELDLY_AO_LP_POOL
    604393901,  # APPLICATION_ID_YIELDLY_CHIP_LP_POOL
    604412989,  # APPLICATION_ID_YIELDLY_FLAMINGO_LP_POOL
    609496314,  # APPLICATION_ID_YIELDLY_WBLN_LP_POOL
    604437391,  # APPLICATION_ID_YIELDLY_BIRDS_LP_POOL
    617728717,  # APPLICATION_ID_YIELDLY_DPANDA_LP_POOL
    618393134,  # APPLICATION_ID_YIELDLY_CURATOR_LP_POOL
    620461252,  # APPLICATION_ID_YIELDLY_ACORN_LP_POOL
    620601402,  # APPLICATION_ID_YIELDLY_CRSD_LP_POOL
    625087406,  # APPLICATION_ID_YIELDLY_NURD_LP_POOL
    620627151,  # APPLICATION_ID_YIELDLY_NEKOS_LP_POOL
    710537301,  # APPLICATION_ID_YIELDLY_COSG_LP_POOL
    717264841,  # APPLICATION_ID_YIELDLY_ALCH_LP_POOL
    724988424,  # APPLICATION_ID_YIELDLY_CHOICE_LP_POOL
    737840564,  # APPLICATION_ID_YIELDLY_ALGO_LP_POOL
    804484890,  # APPLICATION_ID_YIELDLY_ALGO_LP_2_POOL
    873387230,  # APPLICATION_ID_YIELDLY_ALGO_LP_3_POOL
    751372353,  # APPLICATION_ID_YIELDLY_ASASTATS_LP_POOL
    814095794,  # APPLICATION_ID_YIELDLY_ASASTATS_LP_2_POOL
    754147756,  # APPLICATION_ID_YIELDLY_BOARD_LP_POOL
    835516046,  # APPLICATION_ID_YIELDLY_BOARD_LP_2_POOL
    779189004,  # APPLICATION_ID_YIELDLY_ALGX_LP_POOL
    786781576,  # APPLICATION_ID_YIELDLY_XGLI_LP_POOL
    792740888,  # APPLICATION_ID_YIELDLY_KITSU_LP_POOL
    858162134,  # APPLICATION_ID_YIELDLY_KITSU_LP_2_POOL
    872723249,  # APPLICATION_ID_YIELDLY_DBD_LP_POOL
    888156483,  # APPLICATION_ID_YIELDLY_GARDIAN_LP_POOL
]

YIELDLY_TRANSACTION_POOL_CLAIM = "Q0E="         # "CA"
YIELDLY_TRANSACTION_POOL_CLOSE = "Q0FX"         # "CAW"
YIELDLY_TRANSACTION_POOL_BAIL = "YmFpbA=="      # "bail"
YIELDLY_TRANSACTION_POOL_CLAIM_T5 = "Y2xhaW0="  # "claim"
YIELDLY_TRANSACTION_POOL_STAKE_T5 = "c3Rha2U="  # "stake"
YIELDLY_TRANSACTION_POOL_WITHDRAW_T5 = "d2l0aGRyYXc="  # "withdraw"
YIELDLY_TRANSACTION_POOL_STAKE = "Uw=="         # "S"
YIELDLY_TRANSACTION_POOL_WITHDRAW = "Vw=="      # "W"
YIELDLY_TRANSACTION_POOL_DEPOSIT = "RA=="       # "D"


def is_yieldly_transaction(group):
    length = len(group)
    if length < 2 or length > 6:
        return False

    if group[0]["tx-type"] != co.TRANSACTION_TYPE_APP_CALL:
        return False

    if group[1]["tx-type"] == co.TRANSACTION_TYPE_APP_CALL:
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
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if YIELDLY_TRANSACTION_POOL_CLAIM in appl_args:
            app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
            if app_id == APPLICATION_ID_YIELDLY_NLL:
                return _handle_yieldly_nll(group, exporter, txinfo)
            elif app_id == APPLICATION_ID_YIELDLY_YLDY_ALGO_POOL:
                return _handle_yieldly_algo_pool_claim(group, exporter, txinfo)
            elif app_id in YIELDLY_APPLICATIONS:
                return _handle_yieldly_asa_pool_claim(group, exporter, txinfo)
        elif YIELDLY_TRANSACTION_POOL_CLOSE in appl_args:
            # Claims and legacy closeouts are handled the same way
            return _handle_yieldly_asa_pool_claim(group, exporter, txinfo)
        elif YIELDLY_TRANSACTION_POOL_BAIL in appl_args:
            app_transaction = group[0]
            appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
            if (app_transaction[co.TRANSACTION_KEY_APP_CALL]["on-completion"] == "closeout"
                    and "inner-txns" in app_transaction
                    and len(app_transaction["inner-txns"]) == 2):
                return _handle_yieldly_asa_pool_close(group, exporter, txinfo)
            elif YIELDLY_TRANSACTION_POOL_CLAIM_T5 in appl_args:
                return _handle_yieldly_t5_pool_claim(group, exporter, txinfo)
            elif YIELDLY_TRANSACTION_POOL_WITHDRAW_T5 in appl_args:
                return _handle_yieldly_t5_pool_withdraw(group, exporter, txinfo)
        elif YIELDLY_TRANSACTION_POOL_STAKE in appl_args:
            return _handle_yieldly_pool_stake(group, exporter, txinfo)
        elif YIELDLY_TRANSACTION_POOL_WITHDRAW in appl_args:
            return _handle_yieldly_pool_withdraw(group, exporter, txinfo)
        elif YIELDLY_TRANSACTION_POOL_DEPOSIT in appl_args:
            return _handle_yieldly_pool_stake(group, exporter, txinfo)

    app_transaction = group[0]
    txtype = app_transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_APP_CALL:
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if YIELDLY_TRANSACTION_POOL_STAKE_T5 in appl_args:
            return _handle_yieldly_t5_pool_stake(group, exporter, txinfo)

    return handle_unknown(exporter, txinfo)


def _handle_yieldly_nll(group, exporter, txinfo):
    init_transaction = group[0]
    app_transaction = group[1]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    receive_transaction = group[2]
    reward = get_transfer_asset(receive_transaction)

    fee_transaction = group[3]
    fee_amount += fee_transaction["fee"] + fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"]

    export_reward_tx(exporter, txinfo, reward, fee_amount, "Yieldly NLL")


def _handle_yieldly_algo_pool_claim(group, exporter, txinfo):
    init_transaction = group[0]
    app_transaction = group[1]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    app_transaction = group[2]
    fee_amount += app_transaction["fee"]

    axfer_transaction = group[3]
    yldy_reward = get_transfer_asset(axfer_transaction)

    pay_transaction = group[4]
    algo_reward = get_transfer_asset(pay_transaction)

    fee_transaction = group[5]
    fee_amount = fee_transaction["fee"] + fee_transaction[co.TRANSACTION_KEY_PAYMENT]["amount"]

    # Distribute fee over the two transactions
    export_reward_tx(exporter, txinfo, yldy_reward, fee_amount / 2, "Yieldly")
    export_reward_tx(exporter, txinfo, algo_reward, fee_amount / 2, "Yieldly")


def _handle_yieldly_asa_pool_claim(group, exporter, txinfo):
    init_transaction = group[0]
    app_transaction = group[1]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    receive_transaction = group[2]
    reward = get_transfer_asset(receive_transaction)

    export_reward_tx(exporter, txinfo, reward, fee_amount, "Yieldly")


def _handle_yieldly_asa_pool_close(group, exporter, txinfo):
    app_transaction = group[0]
    app_bail_transaction = group[1]
    fee_amount = app_bail_transaction["fee"] + app_transaction["fee"]

    # First inner transaction is a deposit withdraw
    # Second inner transaction is pending rewards claim
    rewards_transaction = app_transaction["inner-txns"][1]
    reward = get_transfer_asset(rewards_transaction)

    export_reward_tx(exporter, txinfo, reward, fee_amount, "Yieldly")


def _handle_yieldly_t5_pool_claim(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[0]
    inner_transactions = app_transaction.get("inner-txns", [])
    length = len(inner_transactions)
    for transaction in inner_transactions:
        reward = get_transfer_asset(transaction)
        export_reward_tx(exporter, txinfo, reward, fee_amount / length, "Yieldly")


def _handle_yieldly_pool_stake(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    send_transaction = group[2]
    send_asset = get_transfer_asset(send_transaction)

    export_stake_tx(exporter, txinfo, send_asset, fee_amount, "Yieldly")


def _handle_yieldly_pool_withdraw(group, exporter, txinfo):
    init_transaction = group[0]
    app_transaction = group[1]
    fee_amount = init_transaction["fee"] + app_transaction["fee"]

    receive_transaction = group[2]
    receive_asset = get_transfer_asset(receive_transaction)

    export_unstake_tx(exporter, txinfo, receive_asset, fee_amount, "Yieldly")


def _handle_yieldly_t5_pool_stake(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    send_transaction = group[1]
    send_asset = get_transfer_asset(send_transaction)

    export_stake_tx(exporter, txinfo, send_asset, fee_amount, "Yieldly")


def _handle_yieldly_t5_pool_withdraw(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[0]
    receive_asset = get_inner_transfer_asset(app_transaction)

    export_unstake_tx(exporter, txinfo, receive_asset, fee_amount, "Yieldly")
