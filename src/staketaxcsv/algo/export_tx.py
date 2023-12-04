
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.common.make_tx import (
    make_airdrop_tx,
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
    make_spend_fee_tx,
    make_stake_tx,
    make_swap_tx,
    make_transfer_in_tx,
    make_transfer_out_tx,
    make_unknown_tx,
    make_unstake_tx,
    make_withdraw_collateral_tx,
)


def _setup_row(row, fee_amount=0, comment=None):
    if fee_amount:
        fee = Algo(fee_amount)
        row.fee = fee.amount
        row.fee_currency = fee.ticker
    if comment:
        row.comment = (comment[:30] + '...') if len(comment) > 32 else comment


def _ingest_row(exporter, row, fee_amount=0, comment=None):
    _setup_row(row, fee_amount, comment)
    exporter.ingest_row(row)


def _should_exclude_tx(asset_list):
    for asset in asset_list:
        if asset is not None:
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

        asset_currency = asset.get_lp_token_currency()
        if asset_currency is not None:
            tokens = asset_currency.split("_")
            if _should_exclude_tx(tokens[2:]):
                return export_exclude_tx(exporter, txinfo)

        return func(*args, **kwargs)

    return inner


@exclude_tx
def export_send_tx(exporter, txinfo, send_asset, fee_amount=0, dest_address=None, comment=None, z_index=0):
    if not send_asset.zero():
        send_asset_currency = (send_asset.get_lp_token_currency() if send_asset.is_lp_token()
                                 else send_asset.ticker)
        row = make_transfer_out_tx(txinfo, send_asset.amount, send_asset_currency, dest_address, z_index)
        _ingest_row(exporter, row, fee_amount, comment)
    elif fee_amount > 0:
        fee = Algo(fee_amount)
        row = make_spend_fee_tx(txinfo, fee.amount, fee.ticker, z_index)
        _ingest_row(exporter, row, comment=comment)


@exclude_tx
@exclude_lp_tx
def export_receive_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    if not receive_asset.zero():
        receive_asset_currency = (receive_asset.get_lp_token_currency() if receive_asset.is_lp_token()
                                    else receive_asset.ticker)
        row = make_transfer_in_tx(txinfo, receive_asset.amount, receive_asset_currency, z_index=z_index)
        _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_reward_tx(exporter, txinfo, reward_asset, fee_amount=0, comment=None, z_index=0):
    if not reward_asset.zero():
        row = make_reward_tx(txinfo, reward_asset.amount, reward_asset.ticker, z_index=z_index)
        _ingest_row(exporter, row, fee_amount, comment)


def export_spend_fee_tx(exporter, txinfo, fee_asset, comment=None, z_index=0):
    row = make_spend_fee_tx(txinfo, fee_asset.amount, fee_asset.ticker, z_index=z_index)
    _ingest_row(exporter, row, comment=comment)


@exclude_tx
@exclude_lp_tx
def export_income_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    if not receive_asset.zero():
        receive_asset_currency = (receive_asset.get_lp_token_currency() if receive_asset.is_lp_token()
                                    else receive_asset.ticker)

        row = make_income_tx(txinfo, receive_asset.amount, receive_asset_currency, z_index=z_index)
        _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_airdrop_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    row = make_airdrop_tx(txinfo, receive_asset.amount, receive_asset.ticker, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount=0, comment=None, z_index=0):
    row = make_swap_tx(
        txinfo,
        send_asset.amount, send_asset.ticker,
        receive_asset.amount, receive_asset.ticker,
        empty_fee=(fee_amount == 0), z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


def create_swap_tx(txinfo, send_asset, receive_asset, fee_amount=0, comment=None, z_index=0):
    if _should_exclude_tx([send_asset, receive_asset]):
        return make_excluded_tx(txinfo)

    row = make_swap_tx(
        txinfo,
        send_asset.amount, send_asset.ticker,
        receive_asset.amount, receive_asset.ticker,
        empty_fee=(fee_amount == 0), z_index=z_index)

    _setup_row(row, fee_amount, comment)

    return row


def export_lp_deposit_tx(
        exporter, txinfo, send_asset_1, send_asset_2, lp_asset,
        fee_amount=0, comment=None, z_index=0):
    lp_asset_currency = lp_asset.get_lp_token_currency()
    if lp_asset_currency is None:
        return export_unknown(exporter, txinfo, z_index)

    if _should_exclude_tx([send_asset_1, send_asset_2, lp_asset]):
        return export_exclude_tx(exporter, txinfo)

    if send_asset_2 is None:
        row = make_lp_deposit_tx(
            txinfo,
            send_asset_1.amount, send_asset_1.ticker,
            lp_asset.amount, lp_asset_currency,
            z_index=z_index)
        _ingest_row(exporter, row, fee_amount, comment)
    else:
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
        exporter, txinfo, lp_asset, receive_asset_1, receive_asset_2,
        fee_amount=0, comment=None, z_index=0):
    lp_asset_currency = lp_asset.get_lp_token_currency()
    if lp_asset_currency is None:
        return export_unknown(exporter, txinfo, z_index)

    if _should_exclude_tx([receive_asset_1, receive_asset_2, lp_asset]):
        return export_exclude_tx(exporter, txinfo)

    if receive_asset_2 is None:
        row = make_lp_withdraw_tx(
            txinfo,
            lp_asset.amount, lp_asset_currency,
            receive_asset_1.amount, receive_asset_1.ticker,
            z_index=z_index)
        _ingest_row(exporter, row, fee_amount, comment)
    else:
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
def export_lp_stake_tx(exporter, txinfo, lp_asset, fee_amount=0, comment=None, z_index=0):
    lp_asset_currency = lp_asset.get_lp_token_currency()

    row = make_lp_stake_tx(txinfo, lp_asset.amount, lp_asset_currency, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
@exclude_lp_tx
def export_lp_unstake_tx(exporter, txinfo, lp_asset, fee_amount=0, comment=None, z_index=0):
    lp_asset_currency = lp_asset.get_lp_token_currency()

    row = make_lp_unstake_tx(txinfo, lp_asset.amount, lp_asset_currency, z_index=z_index)
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
    send_asset_currency = (send_asset.get_lp_token_currency() if send_asset.is_lp_token()
                                else send_asset.ticker)
    row = make_deposit_collateral_tx(txinfo, send_asset.amount, send_asset_currency, z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_withdraw_collateral_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    receive_asset_currency = (receive_asset.get_lp_token_currency() if receive_asset.is_lp_token()
                                else receive_asset.ticker)
    row = make_withdraw_collateral_tx(txinfo, receive_asset.amount, receive_asset_currency, z_index=z_index)
    _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_stake_tx(exporter, txinfo, send_asset, fee_amount=0, comment=None, z_index=0):
    if send_asset.is_lp_token():
        export_lp_stake_tx(exporter, txinfo, send_asset, fee_amount, comment, z_index)
    else:
        row = make_stake_tx(txinfo, send_asset.amount, send_asset.ticker, z_index)
        _ingest_row(exporter, row, fee_amount, comment)


@exclude_tx
def export_unstake_tx(exporter, txinfo, receive_asset, fee_amount=0, comment=None, z_index=0):
    if receive_asset.is_lp_token():
        export_lp_unstake_tx(exporter, txinfo, receive_asset, fee_amount, comment, z_index)
    else:
        row = make_unstake_tx(txinfo, receive_asset.amount, receive_asset.ticker, z_index=z_index)
        _ingest_row(exporter, row, fee_amount, comment)


def export_unknown(exporter, txinfo, z_index=0):
    row = make_unknown_tx(txinfo, z_index)
    exporter.ingest_row(row)


def export_participation_rewards(reward, exporter, txinfo):
    export_reward_tx(exporter, txinfo, reward, comment="Participation Rewards")
