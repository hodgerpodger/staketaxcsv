import base64

from algosdk import encoding
from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import (
    export_borrow_tx,
    export_deposit_collateral_tx,
    export_liquidate_tx,
    export_lp_deposit_tx,
    export_lp_stake_tx,
    export_lp_unstake_tx,
    export_lp_withdraw_tx,
    export_repay_tx,
    export_reward_tx,
    export_swap_tx,
    export_withdraw_collateral_tx,
)
from staketaxcsv.algo.handle_simple import handle_participation_rewards, handle_unknown
from staketaxcsv.algo.handle_transfer import is_governance_reward_transaction
from staketaxcsv.algo.util_algo import get_inner_transfer_asset, get_transfer_asset

# For reference
# https://github.com/Algofiorg/algofi-amm-py-sdk
# https://github.com/Algofiorg/algofi-py-sdk

COMMENT_ALGOFI = "AlgoFi"

APPLICATION_ID_ALGOFI_AMM_MANAGER = 605753404
APPLICATION_ID_ALGOFI_NANOSWAP_MANAGER = 658336870
APPLICATION_ID_ALGOFI_LENDING_MANAGER = 465818260
APPLICATION_ID_ALGOFI_STABILITY_MANAGER = 705663269
APPLICATION_ID_ALGOFI_VALGO_MARKET = 465814318

ALGOFI_AMM_SYMBOL = "AF"

# fetch market variables
# update prices
# update protocol data
# dummy transactions
ALGOFI_NUM_INIT_TXNS = 12

ALGOFI_TRANSACTION_SWAP_EXACT_FOR = "c2Vm"          # "sef"
ALGOFI_TRANSACTION_SWAP_FOR_EXACT = "c2Zl"          # "sfe"
ALGOFI_TRANSACTION_REDEEM_SWAP_RESIDUAL = "cnNy"    # "rsr"

ALGOFI_TRANSACTION_CLAIM_REWARDS = "Y3I="           # "cr"

ALGOFI_TRANSACTION_POOL = "cA=="                    # "p"
ALGOFI_TRANSACTION_REDEEM_POOL_ASSET1_RESIDUAL = "cnBhMXI="   # "rpa1r"
ALGOFI_TRANSACTION_REDEEM_POOL_ASSET2_RESIDUAL = "cnBhMnI="   # "rpa2r"
ALGOFI_TRANSACTION_BURN_ASSET1_OUT = "YmExbw=="     # "ba1o"
ALGOFI_TRANSACTION_BURN_ASSET2_OUT = "YmEybw=="     # "ba2o"


ALGOFI_TRANSACTION_MINT_TO_COLLATERAL = "bXQ="      # "mt"
ALGOFI_TRANSACTION_REMOVE_COLLATERAL_UNDERLYING = "cmN1"      # "rcu"
ALGOFI_TRANSACTION_BORROW = "Yg=="                  # "b"
ALGOFI_TRANSACTION_REPAY_BORROW = "cmI="            # "rb"
ALGOFI_TRANSACTION_LIQUIDATE = "bA=="               # "l"

ALGOFI_TRANSACTION_FLASH_LOAN = "Zmw="              # "fl"

ALGOFI_TRANSACTION_SYNC_VAULT = "c3Y="              # "sv"

ALGOFI_MANAGER_USER_STORAGE_ACCOUNT = "dXNh"        # "usa"

UNDERLYING_ASSETS = {
    # bALGO -> ALGO
    465818547: 0,
    # bUSDC -> USDC
    465818553: 31566704,
    # bgoBTC -> goBTC
    465818554: 386192725,
    # bgoETH -> goETH
    465818555: 386195940,
    # bSTBL -> STBL
    465818563: 465865291,
}

ALGOFI_STAKING_CONTRACTS = {
    # Manager App ID
    482625868: "STBL",
    553869413: "Tinyman STBL-USDC",
    611804624: "STBL-ALGO",
    611869320: "STBL-USDC",
    635813909: "STBL-XET",
    635863793: "STBL-GOBTC",
    635866213: "STBL-GOETH",
    674527132: "OPUL",
    637795072: "STBL-OPUL",
    641500474: "DEFLY",
    639747739: "STBL-DEFLY",
    647785804: "STBL-ZONE",
    661193019: "STBL-USDC",  # NanoSwap
    661204747: "STBL-USDT",  # NanoSwap
    661247364: "USDC-USDT",  # NanoSwap
    705663269: "STBL-USDC",  # NanoSwap Stability
    # Market App ID
    482608867: "STBL",
    553866305: "Tinyman STBL-USDC",
    611801333: "STBL-ALGO",
    611867642: "STBL-USDC",
    635812850: "STBL-XET",
    635860537: "STBL-GOBTC",
    635864509: "STBL-GOETH",
    674526408: "OPUL",
    637793356: "STBL-OPUL",
    641499935: "DEFLY",
    639747119: "STBL-DEFLY",
    647785158: "STBL-ZONE",
    661192413: "STBL-USDC",  # NanoSwap
    661199805: "STBL-USDT",  # NanoSwap
    661207804: "USDC-USDT",  # NanoSwap
    705657303: "STBL-USDC",  # NanoSwap Stability
}


def get_algofi_storage_address(account):
    app_local_state = account.get("apps-local-state", [])
    for app in app_local_state:
        if app["id"] == APPLICATION_ID_ALGOFI_LENDING_MANAGER:
            for keyvalue in app.get("key-value", []):
                if keyvalue["key"] == ALGOFI_MANAGER_USER_STORAGE_ACCOUNT:
                    raw_address = keyvalue["value"]["bytes"]
                    return encoding.encode_address(base64.b64decode(raw_address.strip()))

    return None


def get_algofi_liquidate_transactions(transactions):
    out = []

    for transaction in transactions:
        txtype = transaction["tx-type"]
        if txtype != co.TRANSACTION_TYPE_APP_CALL:
            continue
        appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_LIQUIDATE not in appl_args:
            continue
        out.append(transaction)

    return out


def get_algofi_governance_rewards_transactions(transactions, storage_address):
    out = []

    for transaction in transactions:
        txtype = transaction["tx-type"]
        if txtype != co.TRANSACTION_TYPE_PAYMENT:
            continue
        if not is_governance_reward_transaction(storage_address, [transaction]):
            continue
        out.append(transaction)

    return out


def _is_algofi_zap(group):
    length = len(group)
    if length < 7 or length > 9:
        return False

    i = 0
    txtype = group[i]["tx-type"]
    # Skip opt-in transaction
    if (txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and group[i]["sender"] == group[i][co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        i += 1

    return _is_algofi_swap(group[:i + 2]) and _is_algofi_lp_add(group[i + 2:])


def _is_algofi_swap(group):
    length = len(group)
    if length < 2:
        return False

    i = 0
    txtype = group[i]["tx-type"]
    # Skip opt-in transaction
    if (txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and group[i]["sender"] == group[i][co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        i += 1

    transaction = group[i]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    i += 1
    transaction = group[i]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    foreign_apps = transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]
    if (APPLICATION_ID_ALGOFI_AMM_MANAGER not in foreign_apps
            and APPLICATION_ID_ALGOFI_NANOSWAP_MANAGER not in foreign_apps):
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_SWAP_EXACT_FOR in appl_args:
        return True

    if ALGOFI_TRANSACTION_SWAP_FOR_EXACT not in appl_args:
        return False

    i += 1
    if length < i + 1:
        return False

    transaction = group[i]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return ALGOFI_TRANSACTION_REDEEM_SWAP_RESIDUAL in appl_args


def _is_algofi_claim_rewards(group):
    if len(group) != ALGOFI_NUM_INIT_TXNS + 1:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if (app_id not in [APPLICATION_ID_ALGOFI_LENDING_MANAGER, APPLICATION_ID_ALGOFI_STABILITY_MANAGER]
            and app_id not in ALGOFI_STAKING_CONTRACTS):
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return ALGOFI_TRANSACTION_CLAIM_REWARDS in appl_args


def _is_algofi_lp_add(group):
    length = len(group)
    # Optional ASA opt-in
    if length != 5 and length != 6:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_REDEEM_POOL_ASSET2_RESIDUAL not in appl_args:
        return False

    transaction = group[-2]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_REDEEM_POOL_ASSET1_RESIDUAL not in appl_args:
        return False

    transaction = group[-3]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_POOL not in appl_args:
        return False

    foreign_apps = transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]
    if foreign_apps:
        return (APPLICATION_ID_ALGOFI_AMM_MANAGER in foreign_apps
                    or APPLICATION_ID_ALGOFI_NANOSWAP_MANAGER in foreign_apps)
    return True


def _is_algofi_lp_remove(group):
    if len(group) != 3:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_BURN_ASSET1_OUT not in appl_args:
        return False

    transaction = group[2]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return ALGOFI_TRANSACTION_BURN_ASSET2_OUT in appl_args


def _is_algofi_borrow(group):
    if len(group) != ALGOFI_NUM_INIT_TXNS + 2:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_BORROW not in appl_args:
        return False

    foreign_apps = transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]
    if APPLICATION_ID_ALGOFI_LENDING_MANAGER not in foreign_apps:
        return False

    transaction = group[-2]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id != APPLICATION_ID_ALGOFI_LENDING_MANAGER:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return ALGOFI_TRANSACTION_BORROW in appl_args


def _is_algofi_repay_borrow(group):
    if len(group) != ALGOFI_NUM_INIT_TXNS + 3:
        return False

    transaction = group[-2]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_REPAY_BORROW not in appl_args:
        return False

    foreign_apps = transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]
    if APPLICATION_ID_ALGOFI_LENDING_MANAGER not in foreign_apps:
        return False

    transaction = group[-3]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id != APPLICATION_ID_ALGOFI_LENDING_MANAGER:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return ALGOFI_TRANSACTION_REPAY_BORROW in appl_args


def _is_algofi_deposit_collateral(group):
    if len(group) != ALGOFI_NUM_INIT_TXNS + 3:
        return False

    transaction = group[-2]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_MINT_TO_COLLATERAL not in appl_args:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    foreign_apps = transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]
    if APPLICATION_ID_ALGOFI_LENDING_MANAGER not in foreign_apps and app_id not in ALGOFI_STAKING_CONTRACTS:
        return False

    transaction = group[-3]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id != APPLICATION_ID_ALGOFI_LENDING_MANAGER and app_id not in ALGOFI_STAKING_CONTRACTS:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return ALGOFI_TRANSACTION_MINT_TO_COLLATERAL in appl_args


def _is_algofi_remove_collateral(group):
    if len(group) != ALGOFI_NUM_INIT_TXNS + 2:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_REMOVE_COLLATERAL_UNDERLYING not in appl_args:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    foreign_apps = transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]
    if APPLICATION_ID_ALGOFI_LENDING_MANAGER not in foreign_apps and app_id not in ALGOFI_STAKING_CONTRACTS:
        return False

    transaction = group[-2]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id != APPLICATION_ID_ALGOFI_LENDING_MANAGER and app_id not in ALGOFI_STAKING_CONTRACTS:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    return ALGOFI_TRANSACTION_REMOVE_COLLATERAL_UNDERLYING in appl_args


def _is_algofi_liquidate(group):
    length = len(group)
    # Liquidatee group transactions are trimmed down
    if length != 2 and length != ALGOFI_NUM_INIT_TXNS + 4:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_LIQUIDATE not in appl_args:
        return False

    foreign_apps = transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]
    return APPLICATION_ID_ALGOFI_LENDING_MANAGER in foreign_apps


def _is_algofi_flash_loan(group):
    # Borrow + tx group + repay
    if len(group) < 3:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_FLASH_LOAN not in appl_args:
        return False

    foreign_apps = transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]
    return (APPLICATION_ID_ALGOFI_AMM_MANAGER in foreign_apps
                or APPLICATION_ID_ALGOFI_NANOSWAP_MANAGER in foreign_apps)


def _is_algofi_sync_vault(group):
    if len(group) != ALGOFI_NUM_INIT_TXNS + 2:
        return False

    transaction = group[-1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if ALGOFI_TRANSACTION_SYNC_VAULT not in appl_args:
        return False

    foreign_apps = transaction[co.TRANSACTION_KEY_APP_CALL]["foreign-apps"]
    return APPLICATION_ID_ALGOFI_LENDING_MANAGER in foreign_apps


def is_algofi_transaction(group):
    return (_is_algofi_zap(group)
                or _is_algofi_swap(group)
                or _is_algofi_claim_rewards(group)
                or _is_algofi_lp_add(group)
                or _is_algofi_lp_remove(group)
                or _is_algofi_borrow(group)
                or _is_algofi_repay_borrow(group)
                or _is_algofi_deposit_collateral(group)
                or _is_algofi_remove_collateral(group)
                or _is_algofi_liquidate(group)
                or _is_algofi_flash_loan(group)
                or _is_algofi_sync_vault(group))


def handle_algofi_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    if _is_algofi_zap(group):
        _handle_algofi_zap(group, exporter, txinfo)

    elif _is_algofi_swap(group):
        _handle_algofi_swap(group, exporter, txinfo)

    elif _is_algofi_claim_rewards(group):
        _handle_algofi_claim_rewards(group, exporter, txinfo)

    elif _is_algofi_lp_add(group):
        _handle_algofi_lp_add(group, exporter, txinfo)

    elif _is_algofi_lp_remove(group):
        _handle_algofi_lp_remove(group, exporter, txinfo)

    elif _is_algofi_borrow(group):
        _handle_algofi_borrow(group, exporter, txinfo)

    elif _is_algofi_repay_borrow(group):
        _handle_algofi_repay_borrow(group, exporter, txinfo)

    elif _is_algofi_deposit_collateral(group):
        _handle_algofi_deposit_collateral(group, exporter, txinfo)

    elif _is_algofi_remove_collateral(group):
        _handle_algofi_withdraw_collateral(group, exporter, txinfo)

    elif _is_algofi_liquidate(group):
        _handle_algofi_liquidate(wallet_address, group, exporter, txinfo)

    elif _is_algofi_flash_loan(group):
        _handle_algofi_flash_loan(group, exporter, txinfo)

    elif _is_algofi_sync_vault(group):
        pass

    else:
        handle_unknown(exporter, txinfo)


def _handle_algofi_zap(group, exporter, txinfo):
    i = 0
    txtype = group[i]["tx-type"]
    # Skip opt-in transaction
    if (txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and group[i]["sender"] == group[i][co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        i += 1

    _handle_algofi_swap(group[:i + 2], exporter, txinfo, 0)
    _handle_algofi_lp_add(group[i + 2:], exporter, txinfo, 1)


def _handle_algofi_swap(group, exporter, txinfo, z_index=0):
    txinfo.comment = COMMENT_ALGOFI
    fee_amount = 0
    i = 0
    send_transaction = group[i]
    txtype = send_transaction["tx-type"]
    # Opt-in transaction
    if (txtype == "axfer"
            and send_transaction["sender"] == send_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        fee_amount += send_transaction["fee"]
        i += 1

    z_offset = 0
    # Handle multiple swaps within the group (usual in triangular arbitrage)
    length = len(group)
    while i < length:
        send_transaction = group[i]
        txtype = send_transaction["tx-type"]
        if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
            break

        app_transaction = group[i + 1]
        txtype = app_transaction["tx-type"]
        if txtype != co.TRANSACTION_TYPE_APP_CALL:
            break
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if (ALGOFI_TRANSACTION_SWAP_EXACT_FOR not in appl_args
                and ALGOFI_TRANSACTION_SWAP_FOR_EXACT not in appl_args):
            break
        fee_amount += send_transaction["fee"] + app_transaction["fee"]
        send_asset = get_transfer_asset(send_transaction)
        receive_asset = get_inner_transfer_asset(app_transaction)

        if ALGOFI_TRANSACTION_SWAP_FOR_EXACT in appl_args:
            app_transaction = group[i + 2]
            fee_amount += app_transaction["fee"]
            redeem_asset = get_inner_transfer_asset(app_transaction)
            if redeem_asset is not None:
                send_asset -= redeem_asset
            i += 3
        else:
            i += 2

        export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_ALGOFI, z_index + z_offset)
        z_offset += 1
        fee_amount = 0

    return i


def _handle_algofi_lp_add(group, exporter, txinfo, z_index=0):
    i = 0
    send_transaction = group[i]
    fee_amount = send_transaction["fee"]
    txtype = send_transaction["tx-type"]
    # Opt-in transaction
    if (txtype == "axfer"
            and send_transaction["sender"] == send_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        i += 1
        send_transaction = group[i]
        fee_amount += send_transaction["fee"]
    send_asset_1 = get_transfer_asset(send_transaction)

    i += 1
    send_transaction = group[i]
    fee_amount += send_transaction["fee"]
    send_asset_2 = get_transfer_asset(send_transaction)

    i += 1
    app_transaction = group[i]
    fee_amount += app_transaction["fee"]
    lp_asset = get_inner_transfer_asset(app_transaction)

    i += 1
    app_transaction = group[i]
    fee_amount += app_transaction["fee"]
    redeem_asset_1 = get_inner_transfer_asset(app_transaction)
    if redeem_asset_1 is not None:
        send_asset_1 -= redeem_asset_1

    i += 1
    app_transaction = group[i]
    fee_amount += app_transaction["fee"]
    redeem_asset_2 = get_inner_transfer_asset(app_transaction)
    if redeem_asset_2 is not None:
        send_asset_2 -= redeem_asset_2

    export_lp_deposit_tx(
        exporter, txinfo, ALGOFI_AMM_SYMBOL, send_asset_1, send_asset_2, lp_asset, fee_amount, COMMENT_ALGOFI, z_index)


def _handle_algofi_lp_remove(group, exporter, txinfo):
    send_transaction = group[0]

    fee_amount = send_transaction["fee"]
    lp_asset = get_transfer_asset(send_transaction)

    app_transaction = group[1]
    fee_amount += app_transaction["fee"]
    receive_asset_1 = get_inner_transfer_asset(app_transaction)

    app_transaction = group[2]
    fee_amount += app_transaction["fee"]
    receive_asset_2 = get_inner_transfer_asset(app_transaction)

    export_lp_withdraw_tx(
        exporter, txinfo, ALGOFI_AMM_SYMBOL, lp_asset, receive_asset_1, receive_asset_2, fee_amount, COMMENT_ALGOFI)


def _handle_algofi_claim_rewards(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[-1]
    inner_transactions = app_transaction.get("inner-txns", [])

    length = len(inner_transactions)
    for transaction in inner_transactions:
        reward = get_transfer_asset(transaction)
        export_reward_tx(exporter, txinfo, reward, fee_amount / length, COMMENT_ALGOFI)


def _handle_algofi_borrow(group, exporter, txinfo, z_index=0):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[-1]
    receive_asset = get_inner_transfer_asset(app_transaction)

    export_borrow_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_ALGOFI)


def _handle_algofi_repay_borrow(group, exporter, txinfo, z_index=0):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    send_transaction = group[-1]
    send_asset = get_transfer_asset(send_transaction)

    z_offset = 0
    app_transaction = group[-2]
    txtype = app_transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_APP_CALL:
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_REPAY_BORROW in appl_args:
            residual_asset = get_inner_transfer_asset(app_transaction)
            if residual_asset is not None:
                send_asset -= residual_asset

    export_repay_tx(exporter, txinfo, send_asset, fee_amount, COMMENT_ALGOFI, z_index + z_offset)


def _handle_algofi_liquidate(wallet_address, group, exporter, txinfo):
    fee_amount = 0
    app_transaction = group[-1]
    sender = app_transaction["sender"]
    if sender == wallet_address:
        for transaction in group:
            fee_amount += transaction["fee"]

        send_transaction = group[-2]
        send_asset = get_transfer_asset(send_transaction)

        receive_asset = get_inner_transfer_asset(app_transaction, UNDERLYING_ASSETS)
        export_liquidate_tx(
            exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_ALGOFI + " liquidation")
    else:
        repay_asset = get_inner_transfer_asset(app_transaction, UNDERLYING_ASSETS)
        export_repay_tx(exporter, txinfo, repay_asset, fee_amount, COMMENT_ALGOFI + " liquidation")


def _handle_algofi_flash_loan(group, exporter, txinfo):
    _handle_algofi_borrow(group[:1], exporter, txinfo, 0)
    _handle_algofi_swap(group[1:-1], exporter, txinfo, 1)
    _handle_algofi_repay_borrow(group[-1:], exporter, txinfo, 2)


def _handle_algofi_deposit_collateral(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    send_transaction = group[-1]
    send_asset = get_transfer_asset(send_transaction)

    app_transaction = group[-2]
    app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id in ALGOFI_STAKING_CONTRACTS:
        export_lp_stake_tx(
            exporter, txinfo, send_asset, fee_amount,
            COMMENT_ALGOFI + " " + ALGOFI_STAKING_CONTRACTS[app_id] + " staking")
    else:
        comment = COMMENT_ALGOFI + (" Vault" if app_id == APPLICATION_ID_ALGOFI_VALGO_MARKET else "")
        export_deposit_collateral_tx(exporter, txinfo, send_asset, fee_amount, comment)


def _handle_algofi_withdraw_collateral(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[-1]
    receive_asset = get_inner_transfer_asset(app_transaction)

    app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id in ALGOFI_STAKING_CONTRACTS:
        export_lp_unstake_tx(
            exporter, txinfo, receive_asset, fee_amount,
            COMMENT_ALGOFI + " " + ALGOFI_STAKING_CONTRACTS[app_id] + " unstaking")
    else:
        comment = COMMENT_ALGOFI + (" Vault" if app_id == APPLICATION_ID_ALGOFI_VALGO_MARKET else "")
        export_withdraw_collateral_tx(exporter, txinfo, receive_asset, fee_amount, comment)
