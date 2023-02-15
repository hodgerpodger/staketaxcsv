
from functools import partial
from staketaxcsv.algo.export_tx import export_swap_tx, export_unknown
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_transfer_asset,
    is_app_call,
    is_transfer,
    is_transfer_receiver
)


COMMENT_VESTIGE = "Vestige"

APPLICATION_ID_VESTIGE_SWAP_V1 = 818176933
APPLICATION_ID_VESTIGE_SWAP_V3 = 1026089225

VESTIGE_V1_TRANSACTION_CALL = "Y2FsbA=="  # "call"
# TODO update names when app ABI is published
VESTIGE_V3_TRANSACTION_SWAP_INIT = "NhyEdw=="
VESTIGE_V3_TRANSACTION_SWAP_SWAP = "sogXLw=="
VESTIGE_V3_TRANSACTION_SWAP_FINALIZE = "Exz+tw=="


def _is_vestige_swap_v1(group):
    if len(group) != 2:
        return False

    if not is_transfer(group[0]):
        return False

    return is_app_call(group[1], APPLICATION_ID_VESTIGE_SWAP_V1, VESTIGE_V1_TRANSACTION_CALL)


def _is_vestige_swap_v3(group):
    if len(group) < 4:
        return False

    if not is_app_call(group[0], APPLICATION_ID_VESTIGE_SWAP_V3, VESTIGE_V3_TRANSACTION_SWAP_INIT):
        return False

    if not is_transfer(group[1]):
        return False

    if not is_app_call(group[2], APPLICATION_ID_VESTIGE_SWAP_V3, VESTIGE_V3_TRANSACTION_SWAP_SWAP):
        return False

    return is_app_call(group[-1], APPLICATION_ID_VESTIGE_SWAP_V3, VESTIGE_V3_TRANSACTION_SWAP_FINALIZE)


def is_vestige_transaction(group):
    return _is_vestige_swap_v1(group) or _is_vestige_swap_v3(group)


def handle_vestige_transaction(wallet_address, group, exporter, txinfo):
    if _is_vestige_swap_v1(group):
        _handle_vestige_swap_v1(wallet_address, group, exporter, txinfo)

    elif _is_vestige_swap_v3(group):
        _handle_vestige_swap_v3(wallet_address, group, exporter, txinfo)

    else:
        export_unknown(exporter, txinfo)


def _handle_vestige_swap_v1(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_asset = get_transfer_asset(group[0])
    receive_asset = get_inner_transfer_asset(group[1],
                                             filter=partial(is_transfer_receiver, wallet_address))

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_VESTIGE)


def _handle_vestige_swap_v3(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_asset = get_transfer_asset(group[1])
    receive_asset = get_inner_transfer_asset(group[-1],
                                             filter=partial(is_transfer_receiver, wallet_address))

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_VESTIGE)
