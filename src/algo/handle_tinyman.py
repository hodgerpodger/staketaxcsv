from algo import constants as co
from algo.asset import Algo, Asset
from common.ExporterTypes import TX_TYPE_LP_DEPOSIT, TX_TYPE_LP_WITHDRAW
from common.make_tx import _make_tx_exchange, make_reward_tx, make_swap_tx


def is_tinyman_transaction(group):
    length = len(group)
    if length < 3 or length > 5:
        return False

    if group[1]["tx-type"] != "appl":
        return False

    app_id = group[1]["application-transaction"]["application-id"]
    if (app_id != co.APPLICATION_ID_TINYMAN_v10 and app_id != co.APPLICATION_ID_TINYMAN_v11):
        return False

    return True


def handle_tinyman_transaction(wallet_address, group, exporter, txinfo):
    appl_args = group[1]["application-transaction"]["application-args"]
    # Ignore slippage redeem transactions as they are taken into account in swaps already
    if co.TINYMAN_TRANSACTION_SWAP in appl_args:
        _handle_tinyman_swap(wallet_address, group, exporter, txinfo)
    elif co.TINYMAN_TRANSACTION_LP_ADD in appl_args:
        _handle_tinyman_lp_add(wallet_address, group, exporter, txinfo)
    elif co.TINYMAN_TRANSACTION_LP_REMOVE in appl_args:
        _handle_tinyman_lp_remove(wallet_address, group, exporter, txinfo)


def _handle_tinyman_swap(wallet_address, group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction["payment-transaction"]["amount"] + fee_transaction["fee"]

    reward = Algo(fee_transaction["sender-rewards"])
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)

    slippage_amount = 0
    appl_transaction = group[1]
    fee_amount += appl_transaction["fee"]
    for state in appl_transaction["local-state-delta"]:
        if state["address"] == wallet_address:
            slippage_amount = state["delta"][0]["value"]["uint"]
    if slippage_amount > 0:
        # The slippage redeem group would be composed of:
        #  - A fee payment (payment + tx fee)
        #  - an appl transaction (tx fee)
        #  - either a pay or axfer transaction (tx fee)
        fee_amount += fee_transaction["payment-transaction"]["amount"] + (fee_transaction["fee"] * 3)

    send_transaction = group[2]
    fee_amount += send_transaction["fee"]
    send_asset = _get_transfer_asset(send_transaction)

    receive_transaction = group[3]
    fee_amount += receive_transaction["fee"]
    receive_asset = _get_transfer_asset(receive_transaction)
    receive_asset += slippage_amount

    fee = Algo(fee_amount)
    txinfo.fee = fee.amount
    txinfo.comment = "Tinyman"

    row = make_swap_tx(txinfo, send_asset.amount, send_asset.ticker, receive_asset.amount, receive_asset.ticker)
    exporter.ingest_row(row)


def _get_transfer_asset(transaction):
    amount = 0
    asset_id = 0
    txtype = transaction["tx-type"]
    if txtype == "pay":
        amount = transaction["payment-transaction"]["amount"]
    elif txtype == "axfer":
        amount = transaction["asset-transfer-transaction"]["amount"]
        asset_id = transaction["asset-transfer-transaction"]["asset-id"]

    return Asset(asset_id, amount)


def _handle_tinyman_lp_add(wallet_address, group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction["payment-transaction"]["amount"] + fee_transaction["fee"]

    reward = Algo(fee_transaction["sender-rewards"])
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)

    slippage_amount = 0
    appl_transaction = group[1]
    fee_amount += appl_transaction["fee"]
    for state in appl_transaction["local-state-delta"]:
        if state["address"] == wallet_address:
            slippage_amount = state["delta"][0]["value"]["uint"]
    if slippage_amount > 0:
        # The slippage redeem group would be composed of:
        #  - A fee payment (payment + tx fee)
        #  - an appl transaction (tx fee)
        #  - either a pay or axfer transaction (tx fee)
        fee_amount += fee_transaction["payment-transaction"]["amount"] + (fee_transaction["fee"] * 3)

    send_transaction = group[2]
    fee_amount += send_transaction["fee"]
    send_asset_1 = _get_transfer_asset(send_transaction)

    send_transaction = group[3]
    fee_amount += send_transaction["fee"]
    send_asset_2 = _get_transfer_asset(send_transaction)

    receive_transaction = group[4]
    fee_amount += receive_transaction["fee"]
    lp_asset = _get_transfer_asset(receive_transaction)
    lp_asset += slippage_amount

    fee = Algo(fee_amount / 2)
    txinfo.fee = fee.amount
    txinfo.comment = "Tinyman"

    row = _make_tx_exchange(
        txinfo, send_asset_1.amount, send_asset_1.ticker,
        lp_asset.amount / 2, lp_asset.ticker, TX_TYPE_LP_DEPOSIT)
    exporter.ingest_row(row)

    row = _make_tx_exchange(
        txinfo, send_asset_2.amount, send_asset_2.ticker,
        lp_asset.amount / 2, lp_asset.ticker, TX_TYPE_LP_DEPOSIT)
    exporter.ingest_row(row)


def _handle_tinyman_lp_remove(wallet_address, group, exporter, txinfo):
    fee_transaction = group[0]
    fee_amount = fee_transaction["payment-transaction"]["amount"] + fee_transaction["fee"]

    reward = Algo(fee_transaction["sender-rewards"])
    if not reward.zero():
        row = make_reward_tx(txinfo, reward, reward.ticker)
        exporter.ingest_row(row)

    slippage_amount_1 = 0
    slippage_amount_2 = 0
    appl_transaction = group[1]
    fee_amount += appl_transaction["fee"]
    for state in appl_transaction["local-state-delta"]:
        if state["address"] == wallet_address and len(state["delta"]) == 2:
            slippage_amount_1 = state["delta"][0]["value"]["uint"]
            slippage_amount_2 = state["delta"][1]["value"]["uint"]
    if slippage_amount_1 > 0:
        # The slippage redeem group would be composed of:
        #  - A fee payment (payment + tx fee)
        #  - an appl transaction (tx fee)
        #  - either a pay or axfer transaction (tx fee)
        fee_amount += fee_transaction["payment-transaction"]["amount"] + (fee_transaction["fee"] * 3)
    if slippage_amount_2 > 0:
        fee_amount += fee_transaction["payment-transaction"]["amount"] + (fee_transaction["fee"] * 3)

    receive_transaction = group[2]
    fee_amount += receive_transaction["fee"]
    receive_asset_1 = _get_transfer_asset(receive_transaction)
    # For some reason the order of the assets is inverted in the state delta
    receive_asset_1 += slippage_amount_2

    receive_transaction = group[3]
    fee_amount += receive_transaction["fee"]
    receive_asset_2 = _get_transfer_asset(receive_transaction)
    # For some reason the order of the assets is inverted in the state delta
    receive_asset_2 += slippage_amount_1

    send_transaction = group[4]
    fee_amount += receive_transaction["fee"]
    lp_asset = _get_transfer_asset(send_transaction)

    fee = Algo(fee_amount / 2)
    txinfo.fee = fee.amount
    txinfo.comment = "Tinyman"

    row = _make_tx_exchange(
        txinfo, lp_asset.amount / 2, lp_asset.ticker,
        receive_asset_1.amount, receive_asset_1.ticker,
        TX_TYPE_LP_WITHDRAW)
    exporter.ingest_row(row)

    row = _make_tx_exchange(
        txinfo, lp_asset.amount / 2, lp_asset.ticker,
        receive_asset_2.amount, receive_asset_2.ticker,
        TX_TYPE_LP_WITHDRAW)
    exporter.ingest_row(row)
