import base64
from algosdk import encoding

from algo import constants as co
from algo.asset import Algo
from algo.handle_simple import handle_participation_rewards, handle_unknown
from algo.util_algo import get_transfer_asset
from common.ExporterTypes import TX_TYPE_LP_DEPOSIT, TX_TYPE_LP_WITHDRAW, TX_TYPE_TRADE
from common.make_tx import _make_tx_exchange, make_borrow_tx, make_repay_tx, make_reward_tx, make_swap_tx

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


def get_algofi_storage_address(account):
    app_local_state = account.get("apps-local-state", [])
    for app in app_local_state:
        if app["id"] == APPLICATION_ID_ALGOFI_LENDING_MANAGER:
            for keyvalue in app["key-value"]:
                if keyvalue["key"] == ALGOFI_MANAGER_USER_STORAGE_ACCOUNT:
                    raw_address = keyvalue["value"]["bytes"]
                    return encoding.encode_address(base64.b64decode(raw_address.strip()))

    return None


def is_algofi_transaction(group):
    length = len(group)
    if length > 16:
        return False

    app_transaction = group[-1]
    if app_transaction["tx-type"] == "appl":
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

    # The group size will only be 1 for liquidatee transactions
    if length < 2:
        return False

    app_transaction = group[0]
    if app_transaction["tx-type"] == "appl":
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_FLASH_LOAN in appl_args:
            return True

    app_transaction = group[-2]
    if app_transaction["tx-type"] == "appl":
        appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_REPAY_BORROW in appl_args:
            return True

    return False


def handle_algofi_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    txtype = group[-1]["tx-type"]
    if txtype == "appl":
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

    txtype = group[0]["tx-type"]
    if txtype == "appl":
        appl_args = group[0][co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_FLASH_LOAN in appl_args:
            return _handle_algofi_flash_loan(group, exporter, txinfo)

    txtype = group[-2]["tx-type"]
    if txtype == "appl":
        appl_args = group[-2][co.TRANSACTION_KEY_APP_CALL]["application-args"]
        if ALGOFI_TRANSACTION_REPAY_BORROW in appl_args:
            return _handle_algofi_repay_borrow(group, exporter, txinfo)

    return handle_unknown(exporter, txinfo)


def _handle_algofi_swap(group, exporter, txinfo, z_index=0):
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
    send_asset = get_transfer_asset(send_transaction)

    i += 1
    app_transaction = group[i]
    fee_amount += app_transaction["fee"]
    receive_transaction = app_transaction["inner-txns"][0]
    receive_asset = get_transfer_asset(receive_transaction)

    if i + 1 < len(group):
        app_transaction = group[i + 1]
        txtype = app_transaction["tx-type"]
        if txtype == "appl":
            appl_args = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
            if ALGOFI_TRANSACTION_REDEEM_SWAP_RESIDUAL in appl_args:
                i += 1
                redeem_transaction = app_transaction["inner-txns"][0]
                redeem_asset = get_transfer_asset(redeem_transaction)
                send_asset -= redeem_asset

    txinfo.comment = "AlgoFi"

    row = _make_tx_exchange(
        txinfo, send_asset.amount, send_asset.ticker,
        receive_asset.amount, receive_asset.ticker,
        TX_TYPE_TRADE, z_index=z_index)
    fee = Algo(fee_amount)
    row.fee = fee.amount
    exporter.ingest_row(row)

    return i


def _is_zap_transaction(group):
    i = 0
    txtype = group[i]["tx-type"]
    # Skip opt-in transaction
    if txtype == "axfer" and group[i]["sender"] == group[i][co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]:
        i += 1

    return group[i]["tx-type"] == "axfer" and group[i + 1]["tx-type"] == "appl"


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
    receive_transaction = app_transaction["inner-txns"][0]
    lp_asset = get_transfer_asset(receive_transaction)

    i += 1
    app_transaction = group[i]
    fee_amount += app_transaction["fee"]
    inner_transactions = app_transaction.get("inner-txns", [])
    if len(inner_transactions) > 0:
        redeem_asset_1 = get_transfer_asset(inner_transactions[0])
        send_asset_1 -= redeem_asset_1

    i += 1
    app_transaction = group[i]
    fee_amount += app_transaction["fee"]
    inner_transactions = app_transaction.get("inner-txns", [])
    if len(inner_transactions) > 0:
        redeem_asset_2 = get_transfer_asset(inner_transactions[0])
        send_asset_2 -= redeem_asset_2

    lp_asset_currency = f"LP_{ALGOFI_AMM_SYMBOL}_{send_asset_1.ticker}_{send_asset_2.ticker}"

    fee = Algo(fee_amount / 2)
    txinfo.comment = "AlgoFi"

    row = _make_tx_exchange(
        txinfo, send_asset_1.amount, send_asset_1.ticker,
        lp_asset.amount / 2, lp_asset_currency, TX_TYPE_LP_DEPOSIT)
    row.fee = fee.amount
    exporter.ingest_row(row)

    row = _make_tx_exchange(
        txinfo, send_asset_2.amount, send_asset_2.ticker,
        lp_asset.amount / 2, lp_asset_currency, TX_TYPE_LP_DEPOSIT)
    row.fee = fee.amount
    exporter.ingest_row(row)


def _handle_algofi_lp_remove(group, exporter, txinfo):
    send_transaction = group[0]

    fee_amount = send_transaction["fee"]
    lp_asset = get_transfer_asset(send_transaction)

    app_transaction = group[1]
    fee_amount += app_transaction["fee"]
    receive_transaction = app_transaction["inner-txns"][0]
    receive_asset_1 = get_transfer_asset(receive_transaction)

    app_transaction = group[2]
    fee_amount += app_transaction["fee"]
    receive_transaction = app_transaction["inner-txns"][0]
    receive_asset_2 = get_transfer_asset(receive_transaction)

    lp_asset_currency = f"LP_{ALGOFI_AMM_SYMBOL}_{receive_asset_1.ticker}_{receive_asset_2.ticker}"

    fee = Algo(fee_amount / 2)
    txinfo.comment = "AlgoFi"

    row = _make_tx_exchange(
        txinfo, lp_asset.amount / 2, lp_asset_currency,
        receive_asset_1.amount, receive_asset_1.ticker,
        TX_TYPE_LP_WITHDRAW)
    row.fee = fee.amount
    exporter.ingest_row(row)

    row = _make_tx_exchange(
        txinfo, lp_asset.amount / 2, lp_asset_currency,
        receive_asset_2.amount, receive_asset_2.ticker,
        TX_TYPE_LP_WITHDRAW)
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
    receive_transaction = app_transaction["inner-txns"][0]
    receive_asset = get_transfer_asset(receive_transaction)

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

    row = make_repay_tx(txinfo, send_asset.amount, send_asset.ticker, z_index)
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

        receive_transaction = app_transaction["inner-txns"][0]
        receive_asset = get_transfer_asset(receive_transaction, UNDERLYING_ASSETS)
        row = make_swap_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    else:
        repay_transaction = app_transaction["inner-txns"][0]
        repay_asset = get_transfer_asset(repay_transaction, UNDERLYING_ASSETS)
        row = make_repay_tx(txinfo, repay_asset.amount, repay_asset.ticker)

    txinfo.comment = "AlgoFi liquidation"
    fee = Algo(fee_amount)
    row.fee = fee.amount
    exporter.ingest_row(row)


def _handle_algofi_flash_loan(group, exporter, txinfo):
    _handle_algofi_borrow(group[:1], exporter, txinfo, 0)
    _handle_algofi_swap(group[1:-1], exporter, txinfo, 1)
    _handle_algofi_repay_borrow(group[-1:], exporter, txinfo, 2)
