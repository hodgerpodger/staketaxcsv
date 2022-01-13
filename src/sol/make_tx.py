from common.Exporter import Row
from common.ExporterTypes import (
    TX_TYPE_SOL_LP_DEPOSIT,
    TX_TYPE_SOL_LP_FARM,
    TX_TYPE_SOL_LP_WITHDRAW,
    TX_TYPE_SOL_REWARD_ZERO,
    TX_TYPE_SOL_SERUM_DEX,
    TX_TYPE_SOL_STAKE,
    TX_TYPE_SOL_UNSTAKE,
    TX_TYPE_STAKING,
)
from common.make_tx import _make_tx_exchange, _make_tx_received, _make_tx_sent, make_simple_tx
from sol.constants import CURRENCY_SOL, EXCHANGE_SOLANA_BLOCKCHAIN


def make_sol_reward_tx(timestamp, reward, wallet_address, txid):
    row = Row(
        timestamp=timestamp,
        tx_type=TX_TYPE_STAKING,
        received_amount=reward,
        received_currency=CURRENCY_SOL,
        sent_amount="",
        sent_currency="",
        fee="",
        fee_currency="",
        exchange=EXCHANGE_SOLANA_BLOCKCHAIN,
        wallet_address=wallet_address,
        txid=txid,
        url=""
    )
    return row


def make_lp_deposit_tx(txinfo, sent_amount, sent_currency, lp_amount, lp_currency, txid=None, empty_fee=False,
                       z_index=0):
    return _make_tx_exchange(txinfo, sent_amount, sent_currency, lp_amount, lp_currency, TX_TYPE_SOL_LP_DEPOSIT,
                             txid, empty_fee, z_index=z_index)


def make_lp_withdraw_tx(txinfo, received_amount, received_currency, lp_amount, lp_currency, txid=None, empty_fee=False,
                        z_index=0):
    return _make_tx_exchange(txinfo, lp_amount, lp_currency, received_amount, received_currency,
                             TX_TYPE_SOL_LP_WITHDRAW, txid, empty_fee, z_index=z_index)


def make_lp_farm_tx(txinfo, lp_amount, lp_currency, received_amount, received_currency, txid=None, empty_fee=False,
                    z_index=0):
    return _make_tx_exchange(txinfo, lp_amount, lp_currency, received_amount, received_currency, TX_TYPE_SOL_LP_FARM,
                             txid, empty_fee, z_index=z_index)


def make_stake_tx(txinfo, lp_amount, lp_currency, empty_fee=False, z_index=0):
    return _make_tx_sent(txinfo, lp_amount, lp_currency, TX_TYPE_SOL_STAKE, empty_fee=empty_fee, z_index=z_index)


def make_unstake_tx(txinfo, lp_amount, lp_currency, empty_fee=False, z_index=0):
    return _make_tx_received(txinfo, lp_amount, lp_currency, TX_TYPE_SOL_UNSTAKE, empty_fee=empty_fee, z_index=z_index)


def make_reward_zero_tx(txinfo):
    return make_simple_tx(txinfo, TX_TYPE_SOL_REWARD_ZERO)


def make_serum_dex_transfer_in(txinfo, received_amount, received_currency, empty_fee=False):
    return _make_tx_received(txinfo, received_amount, received_currency, TX_TYPE_SOL_SERUM_DEX, empty_fee=empty_fee)


def make_serum_dex_transfer_out(txinfo, sent_amount, sent_currency, empty_fee=False):
    return _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_SOL_SERUM_DEX, empty_fee=empty_fee)


def make_serum_dex_no_transfer(txinfo):
    return make_simple_tx(txinfo, TX_TYPE_SOL_SERUM_DEX)
