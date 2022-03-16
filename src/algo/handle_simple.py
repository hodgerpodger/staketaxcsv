from algo import constants as co
from algo.asset import Algo
from algo.util_algo import get_transfer_asset
from common.ExporterTypes import TX_TYPE_LP_DEPOSIT, TX_TYPE_LP_WITHDRAW
from common.make_tx import _make_tx_exchange, make_reward_tx, make_swap_tx, make_unknown_tx


def handle_unknown(exporter, txinfo):
    row = make_unknown_tx(txinfo)
    exporter.ingest_row(row)


def handle_participation_rewards(reward, exporter, txinfo):
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        row.fee = 0
        row.comment = "Participation Rewards"
        exporter.ingest_row(row)


def handle_swap(group, exporter, txinfo):
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
    inner_transactions = app_transaction.get("inner-txns", [])
    receive_asset = None
    for transaction in inner_transactions:
        asset = get_transfer_asset(transaction)
        if asset.id == send_asset.id:
            send_asset -= asset
        else:
            receive_asset = asset

    if receive_asset is not None:
        row = make_swap_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    else:
        row = make_unknown_tx(txinfo)

    fee = Algo(fee_amount)
    row.fee = fee.amount
    exporter.ingest_row(row)


def handle_lp_add(amm, group, exporter, txinfo):
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
        lp_asset_currency = f"LP_{amm}_{send_asset_1.ticker}_{send_asset_2.ticker}"

        fee = Algo(fee_amount / 2)
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
    else:
        handle_unknown(exporter, txinfo)


def handle_lp_remove(amm, group, exporter, txinfo):
    send_transaction = group[0]
    fee_amount = send_transaction["fee"]
    lp_asset = get_transfer_asset(send_transaction)

    app_transaction = group[1]
    fee_amount += app_transaction["fee"]
    inner_transactions = app_transaction.get("inner-txns", [])
    if len(inner_transactions) == 2:
        receive_transaction = inner_transactions[0]
        receive_asset_1 = get_transfer_asset(receive_transaction)

        receive_transaction = inner_transactions[1]
        receive_asset_2 = get_transfer_asset(receive_transaction)

        lp_asset_currency = f"LP_{amm}_{receive_asset_1.ticker}_{receive_asset_2.ticker}"

        fee = Algo(fee_amount / 2)

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
    else:
        handle_unknown(exporter, txinfo)
