import base64
from algosdk import encoding

from algo import constants as co
from algo.asset import Algo
from algo.handle_simple import handle_participation_rewards, handle_unknown
from algo.util_algo import get_inner_transfer_asset, get_transfer_asset
from common.make_tx import (
    make_borrow_tx,
    make_deposit_collateral_tx,
    make_liquidate_tx,
    make_lp_deposit_tx,
    make_lp_stake_tx,
    make_lp_unstake_tx,
    make_lp_withdraw_tx,
    make_repay_tx,
    make_reward_tx,
    make_spend_tx,
    make_swap_tx,
    make_withdraw_collateral_tx,
)

# For reference
# https://github.com/Algofiorg/algofi-amm-py-sdk
# https://github.com/Algofiorg/algofi-py-sdk

APPLICATION_ID_ALGOFI_AMM = 605753404
APPLICATION_ID_ALGOFI_LENDING_MANAGER = 465818260

ALGOFI_AMM_SYMBOL = "AF"

ALGOFI_TRANSACTION_SWAP_EXACT_FOR = "c2Vm"          # "sef"
ALGOFI_TRANSACTION_SWAP_FOR_EXACT = "c2Zl"          # "sfe"
ALGOFI_TRANSACTION_REDEEM_SWAP_RESIDUAL = "cnNy"    # "rsr"

ALGOFI_TRANSACTION_CLAIM_REWARDS = "Y3I="           # "cr"

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
    637795072: "STBL-OPUL",
    639747739: "STBL-DEFLY",
    647785804: "STBL-ZONE",
    # Market App ID
    482608867: "STBL",
    553866305: "Tinyman STBL-USDC",
    611801333: "STBL-ALGO",
    611867642: "STBL-USDC",
    635812850: "STBL-XET",
    635860537: "STBL-GOBTC",
    635864509: "STBL-GOETH",
    637793356: "STBL-OPUL",
    639747119: "STBL-DEFLY",
    647785158: "STBL-ZONE",
    # Nano Swap
    658337046: "USDC-STBL",
    659677335: "USDT-STBL",
    659678644: "USDT-USDC",
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


def is_algofi_transaction(group):
    length = len(group)
    if length > 16:
        return False

    app_transaction = group[-1]
    if app_transaction["tx-type"] == co.TRANSACTION_TYPE_APP_CALL:
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        # Swap Exact For
        if ALGOFI_TRANSACTION_SWAP_EXACT_FOR in appl_args:
            return True

        # Swap For Exact
        if ALGOFI_TRANSACTION_REDEEM_SWAP_RESIDUAL in appl_args:
            return True

        # Lending/staking rewards
        if ALGOFI_TRANSACTION_CLAIM_REWARDS in appl_args:
            return True

        # LP mint
        if ALGOFI_TRANSACTION_REDEEM_POOL_ASSET2_RESIDUAL in appl_args:
            return True

        # LP burn
        if ALGOFI_TRANSACTION_BURN_ASSET2_OUT in appl_args:
            return True

        if ALGOFI_TRANSACTION_BORROW in appl_args:
            return True

        if ALGOFI_TRANSACTION_LIQUIDATE in appl_args:
            return True

        if ALGOFI_TRANSACTION_REMOVE_COLLATERAL_UNDERLYING in appl_args:
            return True

    # The group size will only be 1 for liquidatee transactions
    if length < 2:
        return False

    app_transaction = group[0]
    if app_transaction["tx-type"] == co.TRANSACTION_TYPE_APP_CALL:
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_FLASH_LOAN in appl_args:
            return True

    app_transaction = group[-2]
    if app_transaction["tx-type"] == co.TRANSACTION_TYPE_APP_CALL:
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_REPAY_BORROW in appl_args:
            return True

        if ALGOFI_TRANSACTION_MINT_TO_COLLATERAL in appl_args:
            return True

    return False


def handle_algofi_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    txtype = group[-1]["tx-type"]
    if txtype == co.TRANSACTION_TYPE_APP_CALL:
        appl_args = group[-1][co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_SWAP_EXACT_FOR in appl_args or ALGOFI_TRANSACTION_REDEEM_SWAP_RESIDUAL in appl_args:
            return _handle_algofi_swap(group, exporter, txinfo)
        elif ALGOFI_TRANSACTION_CLAIM_REWARDS in appl_args:
            return _handle_algofi_claim_rewards(group, exporter, txinfo)
        elif ALGOFI_TRANSACTION_REDEEM_POOL_ASSET2_RESIDUAL in appl_args:
            return _handle_algofi_lp_add(group, exporter, txinfo)
        elif ALGOFI_TRANSACTION_BURN_ASSET2_OUT in appl_args:
            return _handle_algofi_lp_remove(group, exporter, txinfo)
        elif ALGOFI_TRANSACTION_BORROW in appl_args:
            return _handle_algofi_borrow(group, exporter, txinfo)
        elif ALGOFI_TRANSACTION_LIQUIDATE in appl_args:
            return _handle_algofi_liquidate(wallet_address, group, exporter, txinfo)
        elif ALGOFI_TRANSACTION_REMOVE_COLLATERAL_UNDERLYING in appl_args:
            return _handle_algofi_withdraw_collateral(group, exporter, txinfo)

    txtype = group[0]["tx-type"]
    if txtype == co.TRANSACTION_TYPE_APP_CALL:
        appl_args = group[0][co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_FLASH_LOAN in appl_args:
            return _handle_algofi_flash_loan(group, exporter, txinfo)

    txtype = group[-2]["tx-type"]
    if txtype == co.TRANSACTION_TYPE_APP_CALL:
        appl_args = group[-2][co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_REPAY_BORROW in appl_args:
            return _handle_algofi_repay_borrow(group, exporter, txinfo)
        elif ALGOFI_TRANSACTION_MINT_TO_COLLATERAL in appl_args:
            return _handle_algofi_deposit_collateral(group, exporter, txinfo)

    return handle_unknown(exporter, txinfo)


def _handle_algofi_swap(group, exporter, txinfo, z_index=0):
    txinfo.comment = "AlgoFi"
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

        row = make_swap_tx(
            txinfo, send_asset.amount, send_asset.ticker,
            receive_asset.amount, receive_asset.ticker,
            z_index=z_index + z_offset)
        z_offset += 1
        fee = Algo(fee_amount)
        row.fee = fee.amount
        exporter.ingest_row(row)
        fee_amount = 0

    return i


def _is_zap_transaction(group):
    i = 0
    txtype = group[i]["tx-type"]
    # Skip opt-in transaction
    if (txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and group[i]["sender"] == group[i][co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        i += 1

    return (group[i]["tx-type"] == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and group[i + 1]["tx-type"] == co.TRANSACTION_TYPE_APP_CALL)


def _handle_algofi_lp_add(group, exporter, txinfo):
    i = 0
    if _is_zap_transaction(group):
        i = _handle_algofi_swap(group, exporter, txinfo) + 1

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

    lp_asset_currency = f"LP_{ALGOFI_AMM_SYMBOL}_{send_asset_1.ticker}_{send_asset_2.ticker}"

    fee = Algo(fee_amount / 2)
    txinfo.comment = "AlgoFi"

    row = make_lp_deposit_tx(
        txinfo, send_asset_1.amount, send_asset_1.ticker,
        lp_asset.amount / 2, lp_asset_currency)
    row.fee = fee.amount
    exporter.ingest_row(row)

    row = make_lp_deposit_tx(
        txinfo, send_asset_2.amount, send_asset_2.ticker,
        lp_asset.amount / 2, lp_asset_currency)
    row.fee = fee.amount
    exporter.ingest_row(row)


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

    lp_asset_currency = f"LP_{ALGOFI_AMM_SYMBOL}_{receive_asset_1.ticker}_{receive_asset_2.ticker}"

    fee = Algo(fee_amount / 2)
    txinfo.comment = "AlgoFi"

    row = make_lp_withdraw_tx(
        txinfo, lp_asset.amount / 2, lp_asset_currency,
        receive_asset_1.amount, receive_asset_1.ticker)
    row.fee = fee.amount
    exporter.ingest_row(row)

    row = make_lp_withdraw_tx(
        txinfo, lp_asset.amount / 2, lp_asset_currency,
        receive_asset_2.amount, receive_asset_2.ticker)
    row.fee = fee.amount
    exporter.ingest_row(row)


def _handle_algofi_claim_rewards(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[-1]
    inner_transactions = app_transaction.get("inner-txns", [])

    length = len(inner_transactions)
    if length > 0:
        fee = Algo(fee_amount / length)
        txinfo.comment = "AlgoFi"

        for transaction in inner_transactions:
            reward = get_transfer_asset(transaction)
            if not reward.zero():
                row = make_reward_tx(txinfo, reward, reward.ticker)
                row.fee = fee.amount
                exporter.ingest_row(row)


def _handle_algofi_borrow(group, exporter, txinfo, z_index=0):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[-1]
    receive_asset = get_inner_transfer_asset(app_transaction)

    fee = Algo(fee_amount)
    txinfo.comment = "AlgoFi"

    row = make_borrow_tx(txinfo, receive_asset.amount, receive_asset.ticker, z_index=z_index)
    row.fee = fee.amount
    exporter.ingest_row(row)


def _handle_algofi_repay_borrow(group, exporter, txinfo, z_index=0):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    send_transaction = group[-1]
    send_asset = get_transfer_asset(send_transaction)

    fee = Algo(fee_amount)
    txinfo.comment = "AlgoFi"

    z_offset = 0
    app_transaction = group[-2]
    txtype = app_transaction["tx-type"]
    if txtype == co.TRANSACTION_TYPE_APP_CALL:
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_REPAY_BORROW in appl_args:
            interest_asset = get_inner_transfer_asset(app_transaction)
            if interest_asset is not None:
                row = make_spend_tx(txinfo, interest_asset.amount, interest_asset.ticker, z_index=z_index)
                row.comment = "AlgoFi interest payment"
                exporter.ingest_row(row)
                z_offset = 1

    row = make_repay_tx(txinfo, send_asset.amount, send_asset.ticker, z_index + z_offset)
    row.fee = fee.amount
    exporter.ingest_row(row)


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
        row = make_liquidate_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    else:
        repay_asset = get_inner_transfer_asset(app_transaction, UNDERLYING_ASSETS)
        row = make_repay_tx(txinfo, repay_asset.amount, repay_asset.ticker)

    txinfo.comment = "AlgoFi liquidation"
    fee = Algo(fee_amount)
    row.fee = fee.amount
    exporter.ingest_row(row)


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
        row = make_lp_stake_tx(txinfo, send_asset.amount, send_asset.ticker)
        row.comment = "AlgoFi " + ALGOFI_STAKING_CONTRACTS[app_id] + " staking"
    else:
        row = make_deposit_collateral_tx(txinfo, send_asset.amount, send_asset.ticker)
        row.comment = "AlgoFi"

    fee = Algo(fee_amount)
    row.fee = fee.amount
    exporter.ingest_row(row)


def _handle_algofi_withdraw_collateral(group, exporter, txinfo):
    fee_amount = 0
    for transaction in group:
        fee_amount += transaction["fee"]

    app_transaction = group[-1]
    receive_asset = get_inner_transfer_asset(app_transaction)

    app_transaction = group[-2]
    app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    if app_id in ALGOFI_STAKING_CONTRACTS:
        row = make_lp_unstake_tx(txinfo, receive_asset.amount, receive_asset.ticker)
        row.comment = "AlgoFi " + ALGOFI_STAKING_CONTRACTS[app_id] + " unstaking"
    else:
        row = make_withdraw_collateral_tx(txinfo, receive_asset.amount, receive_asset.ticker)
        row.comment = "AlgoFi"

    fee = Algo(fee_amount)
    row.fee = fee.amount
    exporter.ingest_row(row)
