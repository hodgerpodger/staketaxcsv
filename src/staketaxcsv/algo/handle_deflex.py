import base64
from functools import partial
import hashlib
from staketaxcsv.algo.api_algoindexer import AlgoIndexerAPI
from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.algo.export_tx import (
    export_deposit_collateral_tx,
    export_swap_tx,
    export_unknown,
    export_withdraw_collateral_tx
)
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_transfer_asset,
    is_algo_transfer,
    is_app_call,
    is_transaction_sender,
    is_transfer,
    is_transfer_receiver_non_zero_asset
)

# For reference:
# https://docs.deflex.fi/
# https://github.com/deflex-fi/deflex-abis

COMMENT_DEFLEX = "Deflex"

APPLICATION_ID_DEFLEX_ORDER_ROUTER = [
    989365103,
    956739264,
    951874839,
    892463450,
    1032513697,  # Folks Finance
]
APPLICATION_ID_DEFLEX_REGISTRY = 949209670

DEFLEX_LIMIT_ORDER_APPROVAL_HASH = "fabca7ecf7e45acc21df99d8b98d48d729153272a72d15e2f6b923af3e8458da"

DEFLEX_TRANSACTION_OPT_IN = "TMSORQ=="         # "User_opt_into_assets" ABI selector
DEFLEX_TRANSACTION_SWAP = "P2FHIA=="           # "User_swap" ABI selector
DEFLEX_TRANSACTION_SWAP_FINALIZE = "tTD7Hw=="  # "User_swap_finalize" ABI selector

DEFLEX_TRANSACTION_CREATE_ORDER = "Ai+ORg=="   # "User_create_order" ABI selector
DEFLEX_TRANSACTION_CANCEL_ORDER = "dXwdeg=="   # "User_cancel_order" ABI selector
DEFLEX_TRANSACTION_FILL_ORDER_INIT = "Ynj8hA=="      # "Backend_fill_order_initialize" ABI selector
DEFLEX_TRANSACTION_FILL_ORDER_FINALIZE = "QZXMuQ=="  # "Backend_fill_order_finalize" ABI selector
DEFLEX_TRANSACTION_CLOSE_ESCROW = "jVTQ1A=="   # "Backend_close_escrow" ABI selector

indexer = AlgoIndexerAPI()


def get_deflex_limit_order_apps(account):
    apps = []
    created_apps = account.get("created-apps", [])
    for app in created_apps:
        approval_program = app.get("params", {}).get("approval-program", "")
        approval_hash = hashlib.sha256(base64.b64decode(approval_program)).hexdigest()
        if DEFLEX_LIMIT_ORDER_APPROVAL_HASH == approval_hash:
            apps.append(app["id"])

    return apps


def _is_deflex_routed_swap(wallet_address, group):
    length = len(group)
    if length < 2 or length > 3:
        return False

    transaction = group[0]
    if not is_transfer(transaction):
        return False

    if not is_transaction_sender(wallet_address, transaction):
        return False

    i = 1
    transaction = group[i]
    if is_algo_transfer(transaction) and is_transaction_sender(wallet_address, transaction):
        i += 1

    if i == length:
        return False

    return is_app_call(group[i], APPLICATION_ID_DEFLEX_ORDER_ROUTER, DEFLEX_TRANSACTION_SWAP_FINALIZE)


def _is_deflex_limit_order_fill(group):
    if len(group) != 2:
        return False

    if not is_app_call(group[0], localconfig.deflex_limit_order_apps, DEFLEX_TRANSACTION_FILL_ORDER_FINALIZE):
        return False

    return is_app_call(group[1], APPLICATION_ID_DEFLEX_REGISTRY, DEFLEX_TRANSACTION_CLOSE_ESCROW)


def _is_deflex_limit_order_create(wallet_address, group):
    if len(group) < 4:
        return False

    if not is_app_call(group[-1], localconfig.deflex_limit_order_apps, DEFLEX_TRANSACTION_CREATE_ORDER):
        return False

    transaction = group[-2]
    if not is_transfer(transaction):
        return False

    if not is_transaction_sender(wallet_address, transaction):
        return False

    transaction = group[-3]
    if not is_algo_transfer(transaction):
        return False

    return is_transaction_sender(wallet_address, transaction)


def _is_deflex_limit_order_cancel(group):
    if len(group) != 2:
        return False

    if not is_app_call(group[0], localconfig.deflex_limit_order_apps, DEFLEX_TRANSACTION_CANCEL_ORDER):
        return False

    return is_app_call(group[1], APPLICATION_ID_DEFLEX_REGISTRY, DEFLEX_TRANSACTION_CLOSE_ESCROW)


def is_deflex_transaction(wallet_address, group):
    return (_is_deflex_routed_swap(wallet_address, group)
            or _is_deflex_limit_order_fill(group)
            or _is_deflex_limit_order_create(wallet_address, group)
            or _is_deflex_limit_order_cancel(group))


def handle_deflex_transaction(wallet_address, group, exporter, txinfo):
    if _is_deflex_routed_swap(wallet_address, group):
        _handle_deflex_routed_swap(wallet_address, group, exporter, txinfo)

    elif _is_deflex_limit_order_fill(group):
        _handle_deflex_limit_order_fill(wallet_address, group, exporter, txinfo)

    elif _is_deflex_limit_order_create(wallet_address, group):
        _handle_deflex_limit_order_create(wallet_address, group, exporter, txinfo)

    elif _is_deflex_limit_order_cancel(group):
        _handle_deflex_limit_order_cancel(wallet_address, group, exporter, txinfo)

    else:
        export_unknown(exporter, txinfo)


def _handle_deflex_routed_swap(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_asset = get_transfer_asset(group[0])

    i = 1
    transaction = group[i]
    if is_algo_transfer(transaction) and is_transaction_sender(wallet_address, transaction):
        fee_asset = get_transfer_asset(transaction)
        fee_amount += fee_asset.uint_amount
        i += 1

    receive_asset = get_inner_transfer_asset(group[i],
                                             filter=partial(is_transfer_receiver_non_zero_asset, wallet_address))

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_DEFLEX)


def _handle_deflex_limit_order_fill(wallet_address, group, exporter, txinfo):
    full_group = indexer.get_transactions_by_group(group[0]["group"])

    if not full_group:
        return export_unknown(exporter, txinfo)

    transaction = next((tx for tx in full_group
        if is_app_call(tx, localconfig.deflex_limit_order_apps, DEFLEX_TRANSACTION_FILL_ORDER_INIT)), None)
    if transaction is None:
        return export_unknown(exporter, txinfo)

    send_asset = get_inner_transfer_asset(transaction)

    transaction = full_group[-2]
    receive_asset = get_inner_transfer_asset(transaction,
                                             filter=partial(is_transfer_receiver_non_zero_asset, wallet_address))

    comment = COMMENT_DEFLEX + " Order Fill"
    export_withdraw_collateral_tx(exporter, txinfo, send_asset, 0, comment, 0)
    export_swap_tx(exporter, txinfo, send_asset, receive_asset, 0, comment, 1)


def _handle_deflex_limit_order_create(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_transaction = group[-2]
    send_asset = get_transfer_asset(send_transaction)

    fee_transaction = group[-3]
    fee_asset = get_transfer_asset(fee_transaction)
    fee_amount += fee_asset.uint_amount

    comment = COMMENT_DEFLEX + " Create Order"
    export_deposit_collateral_tx(exporter, txinfo, send_asset, fee_amount, comment, 1)


def _handle_deflex_limit_order_cancel(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    receive_asset = get_inner_transfer_asset(group[0],
                                             filter=partial(is_transfer_receiver_non_zero_asset, wallet_address))
    export_withdraw_collateral_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_DEFLEX + " Order Cancel")
