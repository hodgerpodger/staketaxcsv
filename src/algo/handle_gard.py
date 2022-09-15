from staketaxcsv.algo import constants as co
from staketaxcsv.algo.api_algoindexer import AlgoIndexerAPI
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import (
    export_borrow_tx,
    export_deposit_collateral_tx,
    export_repay_tx,
    export_withdraw_collateral_tx,
)
from staketaxcsv.algo.handle_simple import handle_participation_rewards, handle_unknown
from staketaxcsv.algo.util_algo import get_transfer_asset, get_transfer_close_to_asset, get_transfer_receiver

# For reference
# https://github.com/Tapera-Finance/GARD-BackEnd

APPLICATION_ID_GARD = 684650147

ASSET_ID_GARD = 684649988

GARD_TRANSACTION_NEW_CDP = "TmV3UG9zaXRpb24="   # "NewPosition"
GARD_TRANSACTION_CLOSE_CDP = "Q2xvc2VGZWU="     # "CloseFee"

GARD_ARG_CDP = "AAAAAAAAAAI="  # 2

GARD_OPTIN_AMOUNT = 300000

ADDRESS_GARD_FEE = "MTMJ5ADRK3CFG3HGUI7FS4Y55WGCUO5CRUMVNBZ7FW5IIG6T3IU2VJHUMM"

indexer = AlgoIndexerAPI()

# group_id -> address
cdp_addresses = {}


def _is_gard_new_cdp_transaction(group):
    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    appl_args = transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"]
    if app_id == APPLICATION_ID_GARD and GARD_TRANSACTION_NEW_CDP in appl_args:
        return True

    return False


def _is_gard_close_cdp_transaction(wallet_address, group):
    transaction = group[0]
    asset = get_transfer_asset(transaction)
    if asset is None or asset.id != ASSET_ID_GARD:
        return False

    txsender = transaction["sender"]
    if txsender != wallet_address:
        return False

    pay_transaction = group[1]
    asset = get_transfer_asset(pay_transaction)
    if asset is None or asset.id != co.ASSET_ID_ALGO:
        return False

    logicsig_args = pay_transaction["signature"].get("logicsig", {}).get("args", [])
    return GARD_ARG_CDP in logicsig_args


def _is_gard_add_to_cdp_transaction(wallet_address, group):
    transaction = group[0]
    asset = get_transfer_asset(transaction)
    if asset is None or asset.id != co.ASSET_ID_ALGO:
        return False

    txsender = transaction["sender"]
    txreceiver = get_transfer_receiver(transaction)
    if txsender != wallet_address or txreceiver != ADDRESS_GARD_FEE:
        return False

    mint_transaction = group[1]
    asset = get_transfer_asset(mint_transaction)
    if asset is None or asset.id != ASSET_ID_GARD:
        return False

    logicsig_args = mint_transaction["signature"].get("logicsig", {}).get("args", [])
    return GARD_ARG_CDP in logicsig_args


def _is_gard_cdp_optin_transaction(wallet_address, group):
    length = len(group)
    if length > 2:
        return False

    transaction = group[0]
    asset = get_transfer_asset(transaction)
    if asset is None or asset.id != co.ASSET_ID_ALGO or asset.uint_amount != GARD_OPTIN_AMOUNT:
        return False

    txsender = transaction["sender"]
    if txsender != wallet_address:
        return False

    group_id = transaction["group"]
    if group_id in cdp_addresses:
        return True

    # Weird, but the opt-in app call is sent from a contract account,
    # so it won't appear in the user transaction list.
    full_group = indexer.get_transactions_by_group(group_id)
    length = len(full_group)
    if length < 2 or length > 3:
        return False

    app_transaction = full_group[1]
    txtype = app_transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    op = app_transaction[co.TRANSACTION_KEY_APP_CALL].get("on-completion")
    if app_id != APPLICATION_ID_GARD or op != "optin":
        return False

    txsender = app_transaction["sender"]
    cdp_addresses[group_id] = txsender

    return True


def is_gard_transaction(wallet_address, group):
    length = len(group)
    if length < 1 or length > 4:
        return False

    if (_is_gard_new_cdp_transaction(group)
            or _is_gard_close_cdp_transaction(wallet_address, group)
            or _is_gard_add_to_cdp_transaction(wallet_address, group)
            or _is_gard_cdp_optin_transaction(wallet_address, group)):
        return True

    return False


def handle_gard_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    handle_participation_rewards(reward, exporter, txinfo)

    if _is_gard_new_cdp_transaction(group):
        _handle_gard_new_cdp(group, exporter, txinfo)
    elif _is_gard_add_to_cdp_transaction(wallet_address, group):
        _handle_gard_add_to_cdp(group, exporter, txinfo)
    elif _is_gard_close_cdp_transaction(wallet_address, group):
        _handle_gard_close_cdp(group, exporter, txinfo)
    elif _is_gard_cdp_optin_transaction(wallet_address, group):
        _handle_gard_cdp_optin(group, exporter, txinfo)
    else:
        handle_unknown(exporter, txinfo)


def _handle_gard_new_cdp(group, exporter, txinfo):
    send_transaction = group[1]
    fee_amount = send_transaction["fee"]
    send_asset = get_transfer_asset(send_transaction)

    fee_transaction = group[2]
    mint_fee = get_transfer_asset(fee_transaction)
    fee_amount += mint_fee.uint_amount

    receive_transaction = group[3]
    receive_asset = get_transfer_asset(receive_transaction)

    export_deposit_collateral_tx(exporter, txinfo, send_asset, 0, "Gard", 0)
    export_borrow_tx(exporter, txinfo, receive_asset, fee_amount, "Gard", 1)


def _handle_gard_add_to_cdp(group, exporter, txinfo):
    send_transaction = group[0]
    fee_amount = send_transaction["fee"]
    send_asset = get_transfer_asset(send_transaction)

    receive_transaction = group[1]
    receive_asset = get_transfer_asset(receive_transaction)

    export_deposit_collateral_tx(exporter, txinfo, send_asset, 0, "Gard", 0)
    export_borrow_tx(exporter, txinfo, receive_asset, fee_amount, "Gard", 1)


def _handle_gard_close_cdp(group, exporter, txinfo):
    send_transaction = group[0]
    fee_amount = send_transaction["fee"]
    send_asset = get_transfer_asset(send_transaction)

    receive_transaction = group[1]
    fee_asset = get_transfer_asset(receive_transaction)
    fee_amount += fee_asset.uint_amount

    receive_asset = get_transfer_close_to_asset(receive_transaction)

    export_repay_tx(exporter, txinfo, send_asset, fee_amount, "Gard", 0)
    export_withdraw_collateral_tx(exporter, txinfo, receive_asset, 0, "Gard", 1)


def _handle_gard_cdp_optin(group, exporter, txinfo):
    send_transaction = group[0]
    fee_amount = send_transaction["fee"]
    send_asset = get_transfer_asset(send_transaction)

    export_deposit_collateral_tx(exporter, txinfo, send_asset, fee_amount, "Gard", 0)
