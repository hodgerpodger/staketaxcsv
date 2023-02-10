from functools import partial
from staketaxcsv.algo import constants as co
from staketaxcsv.algo.export_tx import (
    export_lp_deposit_tx,
    export_lp_withdraw_tx,
    export_reward_tx,
    export_unknown,
)
from staketaxcsv.algo.handle_amm import (
    handle_lp_add,
    handle_lp_remove,
    handle_swap,
    is_lp_add_group,
    is_lp_remove_group,
    is_swap_group
)
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_inner_transfer_count,
    get_transfer_asset,
    is_app_call,
    is_asset_optin,
    is_transfer,
    is_transfer_receiver,
    is_transfer_sender
)

APPLICATION_ID_TINYMANV2_VALIDATOR = 1002541853

COMMENT_TINYMANV2 = "Tinyman v2"

TINYMANV2_TRANSACTION_SWAP = "c3dhcA=="                                       # "swap"
TINYMANV2_TRANSACTION_ADD_LIQUIDITY = "YWRkX2xpcXVpZGl0eQ=="                  # "add_liquidity"
TINYMANV2_TRANSACTION_ADD_INITIAL_LIQUIDITY = "YWRkX2luaXRpYWxfbGlxdWlkaXR5"  # "add_initial_liquidity"
TINYMANV2_TRANSACTION_ADD_LIQUIDITY_FLEXIBLE = "ZmxleGlibGU="                 # "flexible"
TINYMANV2_TRANSACTION_ADD_LIQUIDITY_SINGLE = "c2luZ2xl"                       # "single"
TINYMANV2_TRANSACTION_REMOVE_LIQUIDITY = "cmVtb3ZlX2xpcXVpZGl0eQ=="           # "remove_liquidity"


def _is_tinymanv2_swap(wallet_address, group):
    if len(group) != 2:
        return False

    if not is_swap_group(wallet_address, group):
        return False

    return is_app_call(group[-1], APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_SWAP)


def _is_tinymanv2_lp_add(wallet_address, group):
    if not is_lp_add_group(wallet_address, group):
        return False

    return is_app_call(group[-1],
                       APPLICATION_ID_TINYMANV2_VALIDATOR,
                       [TINYMANV2_TRANSACTION_ADD_LIQUIDITY, TINYMANV2_TRANSACTION_ADD_INITIAL_LIQUIDITY])


def _is_tinymanv2_lp_add_single(wallet_address, group):
    length = len(group)
    if length < 2 or length > 3:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    transaction = group[i]
    if not is_transfer(transaction):
        return False

    if not is_transfer_sender(wallet_address, transaction):
        return False

    i += 1
    if i == length:
        return False

    transaction = group[i]
    if not is_app_call(transaction, APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_ADD_LIQUIDITY):
        return False

    return is_app_call(transaction, APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_ADD_LIQUIDITY_SINGLE)


def _is_tinymanv2_lp_remove(wallet_address, group):
    if not is_lp_remove_group(wallet_address, group):
        return False

    return is_app_call(group[-1], APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_REMOVE_LIQUIDITY)


def _is_tinymanv2_lp_remove_single(wallet_address, group):
    length = len(group)
    if length < 2 or length > 4:
        return False

    i = 0
    while i < length and is_asset_optin(group[i]):
        i += 1

    if i == length:
        return False

    transaction = group[i]
    if not is_transfer(transaction):
        return False

    if not is_transfer_sender(wallet_address, transaction):
        return False

    send_asset = get_transfer_asset(transaction)
    if not send_asset.is_lp_token():
        return False

    transaction = group[-1]
    if not is_app_call(transaction, APPLICATION_ID_TINYMANV2_VALIDATOR, TINYMANV2_TRANSACTION_REMOVE_LIQUIDITY):
        return False

    return get_inner_transfer_count(transaction) == 1


def is_tinymanv2_transaction(wallet_address, group):
    return (_is_tinymanv2_swap(wallet_address, group)
                or _is_tinymanv2_lp_add(wallet_address, group)
                or _is_tinymanv2_lp_add_single(wallet_address, group)
                or _is_tinymanv2_lp_remove(wallet_address, group)
                or _is_tinymanv2_lp_remove_single(wallet_address, group))


def handle_tinymanv2_transaction(wallet_address, group, exporter, txinfo):
    txinfo.comment = COMMENT_TINYMANV2

    if _is_tinymanv2_swap(wallet_address, group):
        handle_swap(wallet_address, group, exporter, txinfo)

    elif _is_tinymanv2_lp_add(wallet_address, group):
        handle_lp_add(group, exporter, txinfo)

    elif _is_tinymanv2_lp_add_single(wallet_address, group):
        _handle_tinymanv2_lp_add_single(wallet_address, group, exporter, txinfo)

    elif _is_tinymanv2_lp_remove(wallet_address, group):
        handle_lp_remove(group, exporter, txinfo)

    elif _is_tinymanv2_lp_remove_single(wallet_address, group):
        _handle_tinymanv2_lp_remove_single(wallet_address, group, exporter, txinfo)

    else:
        export_unknown(exporter, txinfo)


def _handle_tinymanv2_lp_add_single(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    send_transaction = group[i]
    send_asset = get_transfer_asset(send_transaction)

    app_transaction = group[i + 1]
    lp_asset = get_inner_transfer_asset(app_transaction,
                                        filter=partial(is_transfer_receiver, wallet_address))
    export_lp_deposit_tx(exporter, txinfo, send_asset, None, lp_asset, fee_amount)


def _handle_tinymanv2_lp_remove_single(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    i = 0
    while is_asset_optin(group[i]):
        i += 1

    send_transaction = group[i]
    lp_asset = get_transfer_asset(send_transaction)

    app_transaction = group[i + 1]
    receive_asset = get_inner_transfer_asset(app_transaction,
                                             filter=partial(is_transfer_receiver, wallet_address))
    export_lp_withdraw_tx(exporter, txinfo, lp_asset, receive_asset, None, fee_amount)
