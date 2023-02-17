from functools import partial
from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.export_tx import export_participation_rewards, export_swap_tx, export_unknown
from staketaxcsv.algo.handle_amm import (
    handle_lp_add,
    handle_lp_remove,
    handle_swap,
    is_lp_add_group,
    is_lp_remove_group,
    is_swap_group
)
from staketaxcsv.algo.transaction import get_fee_amount, get_inner_transfer_asset, get_transfer_asset, is_app_call, is_asset_optin, is_transaction_sender, is_transfer, is_transfer_receiver

APPLICATION_ID_PACT_ROUTER = 887109719

# TODO update names when app ABI is published
PACT_TRANSACTION_ROUTED_SWAP_1 = "hN2OEA=="    # ABI selector
PACT_TRANSACTION_ROUTED_SWAP_2 = "OowGzw=="    # ABI selector

PACT_TRANSACTION_SWAP = "U1dBUA=="           # "SWAP"
PACT_TRANSACTION_LP_ADD = "QURETElR"         # "ADDLIQ"
PACT_TRANSACTION_LP_REMOVE = "UkVNTElR"      # "REMLIQ"


def _is_pact_swap(wallet_address, group):
    if not is_swap_group(wallet_address, group):
        return False

    return is_app_call(group[-1], app_args=PACT_TRANSACTION_SWAP)


def _is_pact_routed_swap(wallet_address, group):
    if len(group) < 2:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    transaction = group[i]
    if not is_transfer(transaction):
        return False

    if not is_transaction_sender(wallet_address, transaction):
        return False

    if is_asset_optin(transaction):
        return False

    return is_app_call(group[-1],
                       APPLICATION_ID_PACT_ROUTER,
                       [PACT_TRANSACTION_ROUTED_SWAP_1, PACT_TRANSACTION_ROUTED_SWAP_2])


def _is_pact_lp_add(wallet_address, group):
    if not is_lp_add_group(wallet_address, group):
        return False

    return is_app_call(group[-1], app_args=PACT_TRANSACTION_LP_ADD)


def _is_pact_lp_remove(wallet_address, group):
    if not is_lp_remove_group(wallet_address, group):
        return False

    return is_app_call(group[-1], app_args=PACT_TRANSACTION_LP_REMOVE)


def is_pact_transaction(wallet_address, group):
    return (_is_pact_routed_swap(wallet_address, group)
                or _is_pact_swap(wallet_address, group)
                or _is_pact_lp_add(wallet_address, group)
                or _is_pact_lp_remove(wallet_address, group))


def handle_pact_transaction(wallet_address, group, exporter, txinfo):
    reward = Algo(group[0]["sender-rewards"])
    export_participation_rewards(reward, exporter, txinfo)

    txinfo.comment = "Pact"
    if _is_pact_routed_swap(wallet_address, group):
        _handle_pact_routed_swap(wallet_address, group, exporter, txinfo)

    elif _is_pact_swap(wallet_address, group):
        handle_swap(wallet_address, group, exporter, txinfo)

    elif _is_pact_lp_add(wallet_address, group):
        handle_lp_add(group, exporter, txinfo)

    elif _is_pact_lp_remove(wallet_address, group):
        handle_lp_remove(group, exporter, txinfo)

    else:
        export_unknown(exporter, txinfo)


def _handle_pact_routed_swap(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    length = len(group)
    i = 0
    while i < length and is_asset_optin(group[i]):
        i += 1

    send_asset = None
    receive_asset = None
    for transaction in group[i:]:
        if is_transfer(transaction):
            asset = get_transfer_asset(transaction)
            send_asset = asset if send_asset is None else send_asset + asset
        elif is_app_call(transaction, app_args=[PACT_TRANSACTION_SWAP,
                                                PACT_TRANSACTION_ROUTED_SWAP_1,
                                                PACT_TRANSACTION_ROUTED_SWAP_2]):
            asset = get_inner_transfer_asset(transaction,
                                             filter=partial(is_transfer_receiver, wallet_address))
            if asset is not None:
                receive_asset = asset if receive_asset is None else receive_asset + asset

    if send_asset is not None and receive_asset is not None:
        export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, "Pact Router")
    else:
        export_unknown(exporter, txinfo)
