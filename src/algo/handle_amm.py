from algo import constants as co
from algo.export_tx import export_lp_deposit_tx, export_lp_withdraw_tx, export_swap_tx
from algo.handle_simple import handle_unknown
from algo.util_algo import get_transfer_asset, get_transfer_receiver


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
    if len(group) != 2:
        return False

    transaction = group[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    txsender = transaction["sender"]
    if txsender != wallet_address:
        return False

    transaction = group[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    inner_transactions = transaction.get("inner-txns", [])
    if len(inner_transactions) != 1:
        return False

    transaction = inner_transactions[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    txreceiver = get_transfer_receiver(transaction)
    if txreceiver != wallet_address:
        return False

    return True


def is_simple_lp_add_group(wallet_address, group):
    length = len(group)
    if length != 3 and length != 4:
        return False

    i = 0
    transaction = group[i]
    txtype = transaction["tx-type"]
    # Opt-in transaction
    if (txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and transaction["sender"] == transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        i += 1

    transaction = group[i]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    i += 1
    txsender = transaction["sender"]
    if txsender != wallet_address:
        return False

    transaction = group[i]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    txsender = transaction["sender"]
    if txsender != wallet_address:
        return False

    i += 1
    transaction = group[i]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_APP_CALL:
        return False

    inner_transactions = transaction.get("inner-txns", [])
    if len(inner_transactions) != 1:
        return False

    transaction = inner_transactions[0]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    txreceiver = get_transfer_receiver(transaction)
    if txreceiver != wallet_address:
        return False

    return True


def is_simple_lp_remove_group(wallet_address, group):
    length = len(group)
    if length < 2 or length > 4:
        return False

    i = 0
    transaction = group[i]
    txtype = transaction["tx-type"]
    # Opt-in transactions
    while (txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and transaction["sender"] == transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        i += 1
        transaction = group[i]
        txtype = transaction["tx-type"]

    if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    txsender = transaction["sender"]
    if txsender != wallet_address:
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
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    txreceiver = get_transfer_receiver(transaction)
    if txreceiver != wallet_address:
        return False

    transaction = inner_transactions[1]
    txtype = transaction["tx-type"]
    if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
        return False

    txreceiver = get_transfer_receiver(transaction)
    if txreceiver != wallet_address:
        return False

    return True


def handle_swap(group, exporter, txinfo):
    fee_amount = 0
    i = 0
    send_transaction = group[i]
    txtype = send_transaction["tx-type"]
    # Opt-in transaction
    if (txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and send_transaction["sender"] == send_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        i += 1
        fee_amount += send_transaction["fee"]

    z_offset = 0
    # Handle multiple swaps within the group (usual in triangular arbitrage)
    length = len(group)
    while i < length:
        send_transaction = group[i]
        txtype = send_transaction["tx-type"]
        if txtype != co.TRANSACTION_TYPE_PAYMENT and txtype != co.TRANSACTION_TYPE_ASSET_TRANSFER:
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
            txtype = transaction["tx-type"]
            if txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER or txtype == co.TRANSACTION_TYPE_PAYMENT:
                asset = get_transfer_asset(transaction)
                if asset.id == send_asset.id:
                    send_asset -= asset
                else:
                    receive_asset = asset

        if receive_asset is not None:
            export_swap_tx(
                exporter, txinfo, send_asset, receive_asset, fee_amount, co.APPL_ARGS_SWAP[swap_arg], z_offset)
        else:
            break

        fee_amount = 0
        i += 2
        z_offset += 1

    if i < length:
        handle_unknown(exporter, txinfo)


def handle_lp_add(amm, group, exporter, txinfo):
    i = 0
    send_transaction = group[i]
    fee_amount = send_transaction["fee"]
    txtype = send_transaction["tx-type"]
    # Opt-in transaction
    if (txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER
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
    inner_transactions = app_transaction.get("inner-txns", [])
    lp_asset = None
    for transaction in inner_transactions:
        asset = get_transfer_asset(transaction)
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
    txtype = send_transaction["tx-type"]
    # Opt-in transactions
    while (txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER
            and send_transaction["sender"] == send_transaction[co.TRANSACTION_KEY_ASSET_TRANSFER]["receiver"]):
        fee_amount += send_transaction["fee"]
        i += 1
        send_transaction = group[i]
        txtype = send_transaction["tx-type"]

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
