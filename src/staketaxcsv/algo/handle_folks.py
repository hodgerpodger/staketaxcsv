from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import (
    export_borrow_tx,
    export_deposit_collateral_tx,
    export_participation_rewards,
    export_repay_tx,
    export_reward_tx,
    export_swap_tx,
    export_unknown,
    export_withdraw_collateral_tx,
)
from staketaxcsv.algo.transaction import (
    get_inner_transfer_asset,
    get_transfer_asset,
    get_transfer_receiver,
    is_app_call,
    is_asset_optin,
    is_transfer
)

# For reference
# https://github.com/Folks-Finance/folks-finance-js-sdk
# https://v1.docs.folks.finance/developer/contracts

COMMENT_FOLKS = "Folks Finance"

ADDRESS_FOLKS_GOVERNANCE_ALGO = [
    "EPYLSPIP3OOKRBFFWKZJWDSPGCYEKUPYBB677GWC2TFYTMU6QP3JZ7OMOQ"
]

APPLICATION_ID_FOLKS_LENDING_MANAGER = 465818260
APPLICATION_ID_FOLKS_GOVERNANCE_3 = 694427622
APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR = [
    793119270
]
APPLICATION_ID_FOLKS_ORACLE_ADAPTERS = [
    689185988,
    751277258,
]

APPLICATION_ID_FOLKS_POOLS = [
    686498781,  # ALGO
    794055220,  # gALGO
    686500029,  # USDC
    686500844,  # USDt
    686501760,  # goBTC
    694405065,  # goETH
    694464549,  # gALGO3
    751285119,  # Planet
    805846536,  # ALGOgALGOPLP
    747237154,  # ALGOUSDCTMP
    747239433,  # ALGOUSDCPLP
    743679535,  # ALGOgALGO3TMP
    743685742,  # ALGOgALGO3PLP
    805843312,  # USDCgALGOTMP
    776179559,  # USDCUSDtTMP
    776176449,  # USDCUSDtPLP
    818026112,  # goBTCgALGOPLP
    818028354,  # goETHgALGOPLP
]

APPLICATION_ID_FOLKS_TOKEN_PAIRS = [
    686541542,  # ALGO-USDC
    686556017,  # ALGO-USDt
    686565241,  # ALGO-goBTC
    695914630,  # ALGO-goETH
    751337142,  # ALGO-Planet
    794069724,  # gALGO-ALGO
    794073216,  # gALGO-USDC
    794075692,  # gALGO-USDt
    794078346,  # gALGO-goBTC
    794079547,  # gALGO-goETH
    794083828,  # gALGO-Planet
    686544126,  # USDC-ALGO
    686571823,  # USDC-USDt
    686577278,  # USDC-goBTC
    695921655,  # USDC-goETH
    751338512,  # USDC-Planet
    686556570,  # USDt-ALGO
    686572578,  # USDt-USDC
    686616139,  # USDt-goBTC
    695926008,  # USDt-goETH
    751339316,  # USDt-Planet
    686565943,  # goBTC-ALGO
    686578002,  # goBTC-USDC
    686616739,  # goBTC-USDt
    695954993,  # goBTC-goETH
    695912626,  # goETH-ALGO
    695919152,  # goETH-USDC
    695924150,  # goETH-USDt
    695953758,  # goETH-goBTC
    694502241,  # gALGO3-ALGO
    694505855,  # gALGO3-USDC
    694509879,  # gALGO3-USDt
    694511513,  # gALGO3-goBTC
    695956892,  # gALGO3-goETH
    751335351,  # Planet-ALGO
    751340276,  # Planet-USDC
    751341083,  # Planet-USDt
    805859260,  # ALGO/gALGOPLP-ALGO
    805860282,  # ALGO/gALGOPLP-USDC
    805861171,  # ALGO/gALGOPLP-USDt
    747248418,  # ALGO/USDCTMP1.1-ALGO
    747252072,  # ALGO/USDCTMP1.1-USDC
    747255122,  # ALGO/USDCTMP1.1-USDt
    747250540,  # ALGO/USDCPLP-ALGO
    747253010,  # ALGO/USDCPLP-USDC
    747254560,  # ALGO/USDCPLP-USDt
    743705087,  # ALGO/gALGO3TMP1.1-ALGO
    743710958,  # ALGO/gALGO3TMP1.1-USDC
    743712504,  # ALGO/gALGO3TMP1.1-USDt
    743708357,  # ALGO/gALGO3PLP-ALGO
    743709872,  # ALGO/gALGO3PLP-USDC
    743713705,  # ALGO/gALGO3PLP-USDt
    805854329,  # USDC/gALGOTMP1.1-ALGO
    805856415,  # USDC/gALGOTMP1.1-USDC
    805857470,  # USDC/gALGOTMP1.1-USDt
    776214410,  # USDC/USDtTMP1.1-ALGO
    776217914,  # USDC/USDtTMP1.1-USDC
    776223117,  # USDC/USDtTMP1.1-USDt
    776215541,  # USDC/USDtPLP-ALGO
    776219872,  # USDC/USDtPLP-USDC
    776224055,  # USDC/USDtPLP-USDt
    818040031,  # goBTC/gALGOPLP-ALGO
    818042616,  # goBTC/gALGOPLP-USDC
    818043183,  # goBTC/gALGOPLP-USDt
    818056982,  # goBTC/gALGOPLP-goBTC
    818060413,  # goBTC/gALGOPLP-goETH
    818041145,  # goETH/gALGOPLP-ALGO
    818045535,  # goETH/gALGOPLP-USDC
    818044129,  # goETH/gALGOPLP-USDt
    818059371,  # goETH/gALGOPLP-goBTC
    818061261,  # goETH/gALGOPLP-goETH
]

APPLICATION_ID_FOLKS_REWARDS_ALGO = 686860954
APPLICATION_ID_FOLKS_REWARDS_USDC = 686862190
APPLICATION_ID_FOLKS_REWARDS_USDT = 686875498
APPLICATION_ID_FOLKS_REWARDS_GOBTC = 686876641
APPLICATION_ID_FOLKS_REWARDS_GOETH = 696044550

FOLKS_REWARDS_AGGREGATORS = [
    APPLICATION_ID_FOLKS_REWARDS_ALGO,
    APPLICATION_ID_FOLKS_REWARDS_USDC,
    APPLICATION_ID_FOLKS_REWARDS_USDT,
    APPLICATION_ID_FOLKS_REWARDS_GOBTC,
    APPLICATION_ID_FOLKS_REWARDS_GOETH,
]

FOLKS_ASSET_ID = [
    686505742,  # fALGO
    686508050,  # fUSDC
    686509463,  # fUSDt
    686510134,  # fgoBTC
    694408528,  # fgoETH
    694474015,  # fgALGO3
    794060802,  # fgALGO
    751289888,  # fPlanet
    805848550,  # fPLP ALGO/gALGO
    747244426,  # fTMP1.1 ALGO/USDC
    747244580,  # fPLP ALGO/USDC
    743689704,  # fTMP1.1 ALGO/gALGO3
    743689819,  # fPLP ALGO/gALGO3
    805848419,  # fTMP1.1 USDC/gALGO
    776184808,  # fTMP1.1 USDC/USDt
    776185076,  # fPLP USDC/USDt
    818036525,  # fPLP goBTC/gALGO
    818036407,  # fPLP goETH/gALGO
]

FOLKS_TRANSACTION_MINT = "bQ=="             # "m"
FOLKS_TRANSACTION_DEPOSIT = "ZA=="          # "d"
FOLKS_TRANSACTION_WITHDRAW = "cg=="         # "r"
FOLKS_TRANSACTION_CLAIM_REWARDS = "Y3I="    # "cr"

FOLKS_TRANSACTION_ADD_ESCROW = "YWU="       # "ae"
FOLKS_TRANSACTION_BORROW = "Yg=="           # "b"
FOLKS_TRANSACTION_REPAY_BORROW = "cmI="     # "rb"
FOLKS_TRANSACTION_INCREASE_BORROW = "aWI="  # "ib"
FOLKS_TRANSACTION_REDUCE_COLLATERAL = "cmM="  # "rc"
FOLKS_TRANSACTION_REWARD_CLAIM = "Yw=="     # "c"
FOLKS_TRANSACTION_REWARD_STAKED_EXCHANGE = "ZQ=="      # "e"
FOLKS_TRANSACTION_REWARD_IMMEDIATE_EXCHANGE = "aWU="   # "ie"

FOLKS_TRANSACTION_GOVERNANCE_MINT = "bh9UTw=="
FOLKS_TRANSACTION_GOVERNANCE_UNMINT = "3c0QwA=="
FOLKS_TRANSACTION_GOVERNANCE_BURN = "ojqoeg=="
FOLKS_TRANSACTION_GOVERNANCE_EARLY_CLAIM = "3jMsVA=="

escrow_addresses = []


def _is_folks_galgo3_optin_transaction(group):
    if len(group) != 2:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    op = transaction[co.TRANSACTION_KEY_APP_CALL].get("on-completion")
    return app_id == APPLICATION_ID_FOLKS_GOVERNANCE_3 and op == "optin"


def _is_folks_galgo3_mint_transaction(group):
    if len(group) != 2:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id == APPLICATION_ID_FOLKS_GOVERNANCE_3 and FOLKS_TRANSACTION_MINT in appl_args


def _is_folks_galgo3_burn_transaction(group):
    if len(group) != 3:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id == APPLICATION_ID_FOLKS_GOVERNANCE_3 and FOLKS_TRANSACTION_BORROW in appl_args


def _is_folks_galgo3_claim_rewards_transaction(group):
    if len(group) != 2:
        return False

    if not is_app_call(group[0], APPLICATION_ID_FOLKS_GOVERNANCE_3, FOLKS_TRANSACTION_CLAIM_REWARDS):
        return False

    return is_transfer(group[1])


def _is_folks_galgo_mint_transaction(group):
    length = len(group)
    if length < 2 or length > 4:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id not in APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if FOLKS_TRANSACTION_GOVERNANCE_MINT not in appl_args:
        return False

    transaction = group[-2]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT:
        return False

    receiver = get_transfer_receiver(transaction)
    return receiver in ADDRESS_FOLKS_GOVERNANCE_ALGO


def _is_folks_galgo_unmint_transaction(group):
    if len(group) != 2:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id not in APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return FOLKS_TRANSACTION_GOVERNANCE_UNMINT in appl_args or FOLKS_TRANSACTION_GOVERNANCE_BURN in appl_args


def _is_folks_galgo_early_claim_transaction(group):
    if len(group) != 1:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id not in APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return FOLKS_TRANSACTION_GOVERNANCE_EARLY_CLAIM in appl_args


def _is_folks_deposit_transaction(group):
    if len(group) != 2:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in APPLICATION_ID_FOLKS_POOLS and FOLKS_TRANSACTION_DEPOSIT in appl_args


def _is_folks_withdraw_transaction(group):
    if len(group) != 2:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in APPLICATION_ID_FOLKS_POOLS and FOLKS_TRANSACTION_WITHDRAW in appl_args


def _is_folks_add_escrow_transaction(wallet_address, group):
    if len(group) != 2:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT:
        return False

    sender = transaction["sender"]
    if sender != wallet_address:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in APPLICATION_ID_FOLKS_TOKEN_PAIRS and FOLKS_TRANSACTION_ADD_ESCROW in appl_args


def _is_folks_borrow_transaction(group):
    if len(group) != 5:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id not in APPLICATION_ID_FOLKS_ORACLE_ADAPTERS:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if app_id not in APPLICATION_ID_FOLKS_POOLS or FOLKS_TRANSACTION_BORROW not in appl_args:
        return False

    transaction = group[2]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in APPLICATION_ID_FOLKS_POOLS and FOLKS_TRANSACTION_BORROW in appl_args


def _is_folks_repay_borrow_transaction(group):
    if len(group) != 4:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if app_id not in APPLICATION_ID_FOLKS_POOLS or FOLKS_TRANSACTION_REPAY_BORROW not in appl_args:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in APPLICATION_ID_FOLKS_POOLS and FOLKS_TRANSACTION_REPAY_BORROW in appl_args


def _is_folks_increase_borrow_transaction(group):
    if len(group) != 4:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id not in APPLICATION_ID_FOLKS_ORACLE_ADAPTERS:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in APPLICATION_ID_FOLKS_POOLS and FOLKS_TRANSACTION_INCREASE_BORROW in appl_args


def _is_folks_increase_collateral_transaction(group):
    if len(group) != 1:
        return False

    transaction = group[0]
    if not is_transfer(transaction):
        return False

    if is_asset_optin(transaction):
        return False

    asset = get_transfer_asset(transaction)
    if asset.id not in FOLKS_ASSET_ID:
        return False

    receiver = get_transfer_receiver(transaction)
    return receiver in escrow_addresses


def _is_folks_reduce_collateral_transaction(group):
    if len(group) != 4:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id not in APPLICATION_ID_FOLKS_ORACLE_ADAPTERS:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in APPLICATION_ID_FOLKS_POOLS and FOLKS_TRANSACTION_REDUCE_COLLATERAL in appl_args


def _is_folks_reward_immediate_exchange_transaction(group):
    if len(group) != 2:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in FOLKS_REWARDS_AGGREGATORS and FOLKS_TRANSACTION_REWARD_IMMEDIATE_EXCHANGE in appl_args


def _is_folks_reward_staked_exchange_transaction(wallet_address, group):
    if len(group) != 3:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT:
        return False

    sender = transaction["sender"]
    if sender != wallet_address:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in FOLKS_REWARDS_AGGREGATORS and FOLKS_TRANSACTION_REWARD_STAKED_EXCHANGE in appl_args


def _is_folks_reward_claim_transaction(group):
    if len(group) != 1:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return app_id in FOLKS_REWARDS_AGGREGATORS and FOLKS_TRANSACTION_REWARD_CLAIM in appl_args


def is_folks_transaction(wallet_address, group):
    return (_is_folks_galgo3_optin_transaction(group)
                or _is_folks_galgo3_mint_transaction(group)
                or _is_folks_galgo3_burn_transaction(group)
                or _is_folks_galgo3_claim_rewards_transaction(group)
                or _is_folks_galgo_mint_transaction(group)
                or _is_folks_galgo_unmint_transaction(group)
                or _is_folks_deposit_transaction(group)
                or _is_folks_withdraw_transaction(group)
                or _is_folks_add_escrow_transaction(wallet_address, group)
                or _is_folks_borrow_transaction(group)
                or _is_folks_repay_borrow_transaction(group)
                or _is_folks_increase_borrow_transaction(group)
                or _is_folks_increase_collateral_transaction(group)
                or _is_folks_reduce_collateral_transaction(group)
                or _is_folks_reward_immediate_exchange_transaction(group)
                or _is_folks_reward_staked_exchange_transaction(wallet_address, group)
                or _is_folks_galgo_early_claim_transaction(group)
                or _is_folks_reward_claim_transaction(group))


def is_folks_escrow_address(address):
    return address in escrow_addresses


def handle_folks_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    export_participation_rewards(reward, exporter, txinfo)

    if _is_folks_galgo3_optin_transaction(group):
        pass

    elif _is_folks_galgo3_mint_transaction(group):
        _handle_folks_galgo3_mint_transaction(group, exporter, txinfo)

    elif _is_folks_galgo3_burn_transaction(group):
        _handle_folks_galgo3_burn_transaction(group, exporter, txinfo)

    elif _is_folks_galgo3_claim_rewards_transaction(group):
        _handle_folks_galgo3_claim_rewards_transaction

    elif _is_folks_galgo_mint_transaction(group):
        _handle_folks_galgo_mint_transaction(group, exporter, txinfo)

    elif _is_folks_galgo_unmint_transaction(group):
        _handle_folks_galgo_unmint_transaction(group, exporter, txinfo)

    elif _is_folks_deposit_transaction(group):
        _handle_folks_deposit_transaction(group, exporter, txinfo)

    elif _is_folks_withdraw_transaction(group):
        _handle_folks_withdraw_transaction(group, exporter, txinfo)

    elif _is_folks_add_escrow_transaction(wallet_address, group):
        _handle_folks_add_escrow_transaction(group)

    elif _is_folks_borrow_transaction(group) or _is_folks_increase_borrow_transaction(group):
        _handle_folks_borrow_transaction(group, exporter, txinfo)

    elif _is_folks_repay_borrow_transaction(group):
        _handle_folks_repay_borrow_transaction(group, exporter, txinfo)

    elif _is_folks_increase_collateral_transaction(group):
        _handle_folks_increase_collateral_transaction(group, exporter, txinfo)

    elif _is_folks_reduce_collateral_transaction(group):
        _handle_folks_reduce_collateral_transaction(group, exporter, txinfo)

    elif _is_folks_reward_immediate_exchange_transaction(group):
        _handle_folks_reward_immediate_exchange_transaction(group, exporter, txinfo)

    elif _is_folks_reward_staked_exchange_transaction(wallet_address, group):
        _handle_folks_reward_staked_exchange_transaction(group, exporter, txinfo)

    elif _is_folks_galgo_early_claim_transaction(group):
        _handle_folks_galgo_early_claim_transaction(group, exporter, txinfo)

    elif _is_folks_reward_claim_transaction(group):
        _handle_folks_reward_claim_transaction(group, exporter, txinfo)

    else:
        export_unknown(exporter, txinfo)


def _handle_folks_galgo3_mint_transaction(group, exporter, txinfo):
    app_transaction = group[0]
    fee_amount = app_transaction["fee"]
    receive_asset = get_inner_transfer_asset(app_transaction)

    send_transaction = group[1]
    send_asset = get_transfer_asset(send_transaction)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_galgo3_burn_transaction(group, exporter, txinfo):
    app_transaction = group[0]
    fee_amount = app_transaction["fee"]

    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)

    send_transaction = group[2]
    send_asset = get_transfer_asset(send_transaction)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_galgo3_claim_rewards_transaction(group, exporter, txinfo):
    app_transaction = group[0]
    fee_amount = app_transaction["fee"]

    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)

    export_reward_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_galgo_mint_transaction(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[-1]
    receive_asset = get_inner_transfer_asset(app_transaction)

    send_transaction = group[-2]
    send_asset = get_transfer_asset(send_transaction)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_galgo_unmint_transaction(group, exporter, txinfo):
    app_transaction = group[1]
    fee_amount = app_transaction["fee"]

    receive_asset = get_inner_transfer_asset(app_transaction)

    send_transaction = group[0]
    send_asset = get_transfer_asset(send_transaction)

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_galgo_early_claim_transaction(group, exporter, txinfo):
    transaction = group[0]
    fee_amount = transaction["fee"]
    reward_asset = get_inner_transfer_asset(transaction)

    export_reward_tx(exporter, txinfo, reward_asset, fee_amount, COMMENT_FOLKS)


# Note: For the moment we are ignoring fTokens as they are
# iliquid tokens that represent a deposit
def _handle_folks_deposit_transaction(group, exporter, txinfo):
    app_transaction = group[0]
    fee_amount = app_transaction["fee"]

    send_transaction = group[1]
    send_asset = get_transfer_asset(send_transaction)

    export_deposit_collateral_tx(exporter, txinfo, send_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_withdraw_transaction(group, exporter, txinfo):
    app_transaction = group[0]
    fee_amount = app_transaction["fee"]
    receive_asset = get_inner_transfer_asset(app_transaction)

    export_withdraw_collateral_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_add_escrow_transaction(group):
    pay_transaction = group[0]
    receiver = get_transfer_receiver(pay_transaction)
    escrow_addresses.append(receiver)


def _handle_folks_borrow_transaction(group, exporter, txinfo):
    app_transaction = group[1]
    fee_amount = app_transaction["fee"]

    app_transaction = group[2]
    receive_asset = get_inner_transfer_asset(app_transaction)

    export_borrow_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_repay_borrow_transaction(group, exporter, txinfo):
    app_transaction = group[0]
    fee_amount = app_transaction["fee"]

    send_transaction = group[3]
    send_asset = get_transfer_asset(send_transaction)

    export_repay_tx(exporter, txinfo, send_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_increase_collateral_transaction(group, exporter, txinfo):
    pass


def _handle_folks_reduce_collateral_transaction(group, exporter, txinfo):
    pass


def _handle_folks_reward_immediate_exchange_transaction(group, exporter, txinfo):
    app_transaction = group[0]
    fee_amount = app_transaction["fee"]

    reward_asset = get_inner_transfer_asset(app_transaction)

    export_reward_tx(exporter, txinfo, reward_asset, fee_amount, COMMENT_FOLKS)


def _handle_folks_reward_staked_exchange_transaction(group, exporter, txinfo):
    pass


def _handle_folks_reward_claim_transaction(group, exporter, txinfo):
    transaction = group[0]
    fee_amount = transaction["fee"]

    reward_asset = get_inner_transfer_asset(transaction)

    export_reward_tx(exporter, txinfo, reward_asset, fee_amount, COMMENT_FOLKS)
