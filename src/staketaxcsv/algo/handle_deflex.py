from functools import partial
from staketaxcsv.algo.export_tx import export_swap_tx, export_unknown
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_transfer_asset,
    is_app_call,
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
    892463450
]

DEFLEX_TRANSACTION_OPT_IN = "TMSORQ=="         # "User_opt_into_assets" ABI selector
DEFLEX_TRANSACTION_SWAP = "P2FHIA=="           # "User_swap" ABI selector
DEFLEX_TRANSACTION_SWAP_FINALIZE = "tTD7Hw=="  # "User_swap_finalize" ABI selector


def _is_deflex_routed_swap(wallet_address, group):
    if len(group) != 2:
        return False

    transaction = group[0]
    if not is_transfer(transaction):
        return False
    if wallet_address != transaction["sender"]:
        return False

    return is_app_call(group[1], APPLICATION_ID_DEFLEX_ORDER_ROUTER, DEFLEX_TRANSACTION_SWAP_FINALIZE)


def _is_deflex_limit_swap(wallet_address, group):
    return False


def is_deflex_transaction(wallet_address, group):
    return (_is_deflex_routed_swap(wallet_address, group)
            or _is_deflex_limit_swap(wallet_address, group))


def handle_deflex_transaction(wallet_address, group, exporter, txinfo):
    if _is_deflex_routed_swap(wallet_address, group):
        _handle_deflex_routed_swap(wallet_address, group, exporter, txinfo)

    elif _is_deflex_limit_swap(wallet_address, group):
        _handle_deflex_limit_swap(wallet_address, group, exporter, txinfo)

    else:
        export_unknown(exporter, txinfo)


def _handle_deflex_routed_swap(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_transaction = group[0]
    send_asset = get_transfer_asset(send_transaction)

    app_transaction = group[1]
    receive_asset = get_inner_transfer_asset(app_transaction,
                                             filter=partial(is_transfer_receiver_non_zero_asset, wallet_address))

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_DEFLEX)


def _handle_deflex_limit_swap(wallet_address, group, exporter, txinfo):
    pass
