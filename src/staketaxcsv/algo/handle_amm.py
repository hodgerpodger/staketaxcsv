from functools import partial
from staketaxcsv.algo import constants as co
from staketaxcsv.algo.export_tx import create_swap_tx, export_lp_deposit_tx, export_lp_withdraw_tx, export_swap_tx
from staketaxcsv.algo.handle_simple import handle_unknown
from staketaxcsv.algo.handle_transfer import handle_transfer_transactions
from staketaxcsv.algo.transaction import (
    get_inner_transfer_asset,
    get_transfer_asset,
    is_asset_optin,
    is_transfer,
    is_transfer_receiver,
    is_transfer_receiver_non_zero_asset,
    is_transfer_sender
)


def _get_swap_arg(transaction):
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    appl_args = set(transaction[co.TRANSACTION_KEY_APP_CALL]["application-args"])
    if not appl_args:
        return co.UNKNOWN_TRANSACTION

    swap_args = set(co.APPL_ARGS_SWAP.keys())
    intersection = swap_args & appl_args
    if intersection:
        return next(iter(intersection))

    return None


def is_simple_swap_group(wallet_address, group):
    length = len(group)
    if length < 2:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    while i < length:
        transaction = group[i]
        if not is_transfer(transaction):
            return False

        if not is_transfer_sender(wallet_address, transaction):
            return False

        i += 1
        if i == length:
            return False

        receive_asset = get_inner_transfer_asset(group[i],
                                                 filter=partial(is_transfer_receiver_non_zero_asset, wallet_address))

        if receive_asset is None:
            return False

        i += 1

    return True


def is_simple_lp_add_group(wallet_address, group):
    length = len(group)
    if length != 3 and length != 4:
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
    transaction = group[i]
    if not is_transfer(transaction):
        return False

    if not is_transfer_sender(wallet_address, transaction):
        return False

    i += 1
    if i == length:
        return False

    receive_asset = get_inner_transfer_asset(group[i],
                                             filter=partial(is_transfer_receiver, wallet_address))

    return receive_asset is not None


def is_simple_lp_remove_group(wallet_address, group):
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

    i += 1
    transaction = group[i]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    inner_transactions = transaction.get("inner-txns", [])
    if len(inner_transactions) != 2:
        return False

    transaction = inner_transactions[0]
    if not is_transfer(transaction):
        return False

    if not is_transfer_receiver(wallet_address, transaction):
        return False

    transaction = inner_transactions[1]
    if not is_transfer(transaction):
        return False

    if not is_transfer_receiver(wallet_address, transaction):
        return False

    return True


def handle_swap(wallet_address, group, exporter, txinfo):
    fee_amount = 0
    i = 0
    send_transaction = group[i]
    if is_asset_optin(group[i]):
        i += 1
        fee_amount += send_transaction["fee"]

    rows = []
    z_offset = 0
    # Handle multiple swaps within the group (usual in triangular arbitrage)
    length = len(group)
    while i < length:
        send_transaction = group[i]
        if not is_transfer(send_transaction) or not is_transfer_sender(wallet_address, send_transaction):
            break

        app_transaction = group[i + 1]
        # TODO this should be done with app ids rather than args
        swap_arg = _get_swap_arg(app_transaction)
        if swap_arg is None:
            break
        fee_amount += send_transaction["fee"] + app_transaction["fee"]
        send_asset = get_transfer_asset(send_transaction)
        inner_transactions = app_transaction.get("inner-txns", [])
        receive_asset = None
        for transaction in inner_transactions:
            if is_transfer(transaction) and is_transfer_receiver(wallet_address, transaction):
                asset = get_transfer_asset(transaction)
                if asset is None or asset.zero():
                    continue

                if asset.id == send_asset.id:
                    send_asset -= asset
                else:
                    receive_asset = asset

        if receive_asset is None:
            break

        row = create_swap_tx(txinfo, send_asset, receive_asset, fee_amount, co.APPL_ARGS_SWAP[swap_arg], z_offset)
        rows.append(row)

        fee_amount = 0
        i += 2
        z_offset += 1

    if i < length:
        handle_transfer_transactions(wallet_address, group, exporter, txinfo)
    else:
        for row in rows:
            exporter.ingest_row(row)


def handle_lp_add(amm, group, exporter, txinfo):
    i = 0
    send_transaction = group[i]
    fee_amount = send_transaction["fee"]
    if is_asset_optin(group[i]):
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
    inner_transactions = app_transaction.get("inner-txns", [])
    lp_asset = None
    for transaction in inner_transactions:
        asset = get_transfer_asset(transaction)
        if asset is None:
            continue

        if asset.id == send_asset_1.id:
            send_asset_1 -= asset
        elif asset.id == send_asset_2.id:
            send_asset_2 -= asset
        else:
            lp_asset = asset

    if lp_asset is not None:
        export_lp_deposit_tx(exporter, txinfo, amm, send_asset_1, send_asset_2, lp_asset, fee_amount)
    else:
        handle_unknown(exporter, txinfo)


def handle_lp_remove(amm, group, exporter, txinfo):
    i = 0
    fee_amount = 0
    send_transaction = group[i]
    while is_asset_optin(group[i]):
        fee_amount += send_transaction["fee"]
        i += 1
        send_transaction = group[i]

    fee_amount = send_transaction["fee"]
    lp_asset = get_transfer_asset(send_transaction)

    i += 1
    app_transaction = group[i]
    fee_amount += app_transaction["fee"]
    inner_transactions = app_transaction.get("inner-txns", [])
    if len(inner_transactions) == 2:
        receive_transaction = inner_transactions[0]
        receive_asset_1 = get_transfer_asset(receive_transaction)

        receive_transaction = inner_transactions[1]
        receive_asset_2 = get_transfer_asset(receive_transaction)

        export_lp_withdraw_tx(exporter, txinfo, amm, lp_asset, receive_asset_1, receive_asset_2, fee_amount)
    else:
        handle_unknown(exporter, txinfo)
