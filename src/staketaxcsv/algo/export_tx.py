
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.common.make_tx import (
    make_borrow_tx,
    make_deposit_collateral_tx,
    make_excluded_tx,
    make_income_tx,
    make_liquidate_tx,
    make_lp_deposit_tx,
    make_lp_stake_tx,
    make_lp_unstake_tx,
    make_lp_withdraw_tx,
    make_repay_tx,
    make_reward_tx,
    make_spend_tx,
    make_stake_tx,
    make_swap_tx,
    make_transfer_in_tx,
    make_transfer_out_tx,
    make_unstake_tx,
    make_withdraw_collateral_tx,
)

lp_tickers = {}


def _ingest_row(exporter, row, fee_amount=0, comment=None):
    if fee_amount:
        fee = Algo(fee_amount)
        row.fee = fee.amount
    if comment:
        row.comment = comment
    exporter.ingest_row(row)


def _should_exclude_tx(asset_list):
    for asset in asset_list:
        ticker = asset.ticker if isinstance(asset, Asset) else asset
        if ticker.lower() in localconfig.exclude_asas:
            return True
    return False


def export_exclude_tx(exporter, txinfo):
    row = make_excluded_tx(txinfo)
    _ingest_row(exporter, row)


def exclude_tx(func):
    def inner(*args, **kwargs):
        asset_list = [arg for arg in args[2:] if isinstance(arg, Asset)]
        exporter = args[0]
        txinfo = args[1]
        if _should_exclude_tx(asset_list):
            return export_exclude_tx(exporter, txinfo)

        return func(*args, **kwargs)

    return inner


def exclude_lp_tx(func):
    def inner(*args, **kwargs):
        exporter = args[0]
        txinfo = args[1]
        asset = args[2]

        asset_currency = lp_tickers.get(asset.id, asset.ticker)
        if asset_currency.startswith("LP_"):
            tokens = asset_currency.split("_")
            if _should_exclude_tx(tokens[2:]):
                return export_exclude_tx(exporter, txinfo)

        return func(*args, **kwargs)

    return inner


@exclude_tx
def export_send_tx(exporter, txinfo, send_asset, fee_amount=0, dest_address=None, comment=None, z_index=0):
    if not send_asset.zero():
        row = make_transfer_out_tx(txinfo, send_asset.amount, send_asset.ticker, dest_address, z_index)
        _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_receive_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    if not receive_asset.zero():
        row = make_transfer_in_tx(txinfo, receive_asset.amount, receive_asset.ticker, z_index=z_index)
        _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_reward_tx(exporter, txinfo, reward_asset, fee_amount=0, comment=None, z_index=0):
    if not reward_asset.zero():
        row = make_reward_tx(txinfo, reward_asset.amount, reward_asset.ticker, z_index=z_index)
        _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_spend_tx(exporter, txinfo, send_asset, fee_amount=0, comment=None, z_index=0):
    row = make_spend_tx(txinfo, send_asset.amount, send_asset.ticker, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
@exclude_lp_tx
def export_income_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    receive_asset_currency = lp_tickers.get(receive_asset.id, receive_asset.ticker)

    row = make_income_tx(txinfo, receive_asset.amount, receive_asset_currency, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount=0, comment=None, z_index=0):
    row = make_swap_tx(
        txinfo,
        send_asset.amount, send_asset.ticker,
        receive_asset.amount, receive_asset.ticker,
        z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


def export_lp_deposit_tx(
        exporter, txinfo, amm_symbol, send_asset_1, send_asset_2, lp_asset,
        fee_amount=0, comment=None, z_index=0):
    lp_asset_currency = f"LP_{amm_symbol}_{send_asset_1.ticker}_{send_asset_2.ticker}"
    lp_tickers[lp_asset.id] = lp_asset_currency
    if _should_exclude_tx([send_asset_1, send_asset_2, lp_asset]):
        return export_exclude_tx(exporter, txinfo)

    row = make_lp_deposit_tx(
        txinfo,
        send_asset_1.amount, send_asset_1.ticker,
        lp_asset.amount / 2, lp_asset_currency,
        z_index=z_index)
    _ingest_row(exporter, row, fee_amount / 2, comment)

    row = make_lp_deposit_tx(
        txinfo,
        send_asset_2.amount, send_asset_2.ticker,
        lp_asset.amount / 2, lp_asset_currency,
        z_index=z_index + 1)
    _ingest_row(exporter, row, fee_amount / 2, comment)


def export_lp_withdraw_tx(
        exporter, txinfo, amm_symbol, lp_asset, receive_asset_1, receive_asset_2,
        fee_amount=0, comment=None, z_index=0):
    lp_asset_currency = f"LP_{amm_symbol}_{receive_asset_1.ticker}_{receive_asset_2.ticker}"
    lp_tickers[lp_asset.id] = lp_asset_currency
    if _should_exclude_tx([receive_asset_1, receive_asset_2, lp_asset]):
        return export_exclude_tx(exporter, txinfo)

    row = make_lp_withdraw_tx(
        txinfo,
        lp_asset.amount / 2, lp_asset_currency,
        receive_asset_1.amount, receive_asset_1.ticker,
        z_index=z_index)
    _ingest_row(exporter, row, fee_amount / 2, comment)

    row = make_lp_withdraw_tx(
        txinfo,
        lp_asset.amount / 2, lp_asset_currency,
        receive_asset_2.amount, receive_asset_2.ticker,
        z_index=z_index + 1)
    _ingest_row(exporter, row, fee_amount / 2, comment)


@exclude_tx
@exclude_lp_tx
def export_lp_stake_tx(exporter, txinfo, send_asset, fee_amount=0, comment=None, z_index=0):
    send_asset_currency = lp_tickers.get(send_asset.id, send_asset.ticker)

    row = make_lp_stake_tx(txinfo, send_asset.amount, send_asset_currency, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
@exclude_lp_tx
def export_lp_unstake_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    receive_asset_currency = lp_tickers.get(receive_asset.id, receive_asset.ticker)

    row = make_lp_unstake_tx(txinfo, receive_asset.amount, receive_asset_currency, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_borrow_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    row = make_borrow_tx(txinfo, receive_asset.amount, receive_asset.ticker, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_repay_tx(exporter, txinfo, send_asset, fee_amount=0, comment=None, z_index=0):
    row = make_repay_tx(txinfo, send_asset.amount, send_asset.ticker, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_liquidate_tx(exporter, txinfo, send_asset, receive_asset, fee_amount=0, comment=None, z_index=0):
    row = make_liquidate_tx(
        txinfo,
        send_asset.amount, send_asset.ticker,
        receive_asset.amount, receive_asset.ticker,
        z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_deposit_collateral_tx(exporter, txinfo, send_asset, fee_amount=0, comment=None, z_index=0):
    row = make_deposit_collateral_tx(txinfo, send_asset.amount, send_asset.ticker, z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_withdraw_collateral_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    row = make_withdraw_collateral_tx(txinfo, receive_asset.amount, receive_asset.ticker, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_stake_tx(exporter, txinfo, send_asset, fee_amount=0, comment=None, z_index=0):
    send_asset_currency = lp_tickers.get(send_asset.id, send_asset.ticker)
    row = make_stake_tx(txinfo, send_asset.amount, send_asset_currency, z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_unstake_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    receive_asset_currency = lp_tickers.get(receive_asset.id, receive_asset.ticker)
    row = make_unstake_tx(txinfo, receive_asset.amount, receive_asset_currency, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)
