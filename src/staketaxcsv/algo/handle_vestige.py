
from functools import partial
from staketaxcsv.algo.export_tx import export_swap_tx
from staketaxcsv.algo.handle_simple import handle_unknown
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_transfer_asset,
    is_app_call,
    is_transfer,
    is_transfer_receiver
)


COMMENT_VESTIGE = "Vestige"

APPLICATION_ID_VESTIGE_SWAP = 818176933

VESTIGE_TRANSACTION_CALL = "Y2FsbA=="  # "call"


def _is_vestige_swap(group):
    if len(group) != 2:
        return False

    if not is_transfer(group[0]):
        return False

    return is_app_call(group[1], APPLICATION_ID_VESTIGE_SWAP, VESTIGE_TRANSACTION_CALL)


def is_vestige_transaction(group):
    return _is_vestige_swap(group)


def handle_vestige_transaction(wallet_address, group, exporter, txinfo):
    if _is_vestige_swap(group):
        _handle_vestige_swap(wallet_address, group, exporter, txinfo)

    else:
        handle_unknown(exporter, txinfo)


def _handle_vestige_swap(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_asset = get_transfer_asset(group[0])
    receive_asset = get_inner_transfer_asset(group[1],
                                             filter=partial(is_transfer_receiver, wallet_address))

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_VESTIGE)
