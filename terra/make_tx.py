
from common.Exporter import (
    TX_TYPE_STAKING, TX_TYPE_AIRDROP, TX_TYPE_TRADE, TX_TYPE_TRANSFER,
    TX_TYPE_LP_DEPOSIT, TX_TYPE_LP_WITHDRAW, TX_TYPE_LP_STAKE, TX_TYPE_LP_UNSTAKE,
    TX_TYPE_EARN_DEPOSIT, TX_TYPE_EARN_WITHDRAW, TX_TYPE_BORROW, TX_TYPE_REPAY,
    TX_TYPE_GOV_STAKE, TX_TYPE_GOV_UNSTAKE,
    TX_TYPE_BOND, TX_TYPE_DEPOSIT_COLLATERAL, TX_TYPE_WITHDRAW_COLLATERAL,
    TX_TYPE_UNBOND_WITHDRAW, TX_TYPE_UNBOND, TX_TYPE_UNBOND_INSTANT,
    TX_TYPE_NFT_MINT, TX_TYPE_NFT_OFFER_SELL, TX_TYPE_NFT_WITHDRAW,
    TX_TYPE_NFT_DEPOSIT
)
from terra.constants import CUR_UST, CUR_LUNA, CUR_AUST
from common.make_tx import _make_tx_received, _make_tx_sent, _make_tx_exchange, make_simple_tx


def make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency,
                 txid=None, empty_fee=False):
    # Special case: treat swap into bLUNA as bond transaction
    if received_currency.upper() == "BLUNA" and sent_currency == CUR_LUNA:
        return make_bond_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    elif received_currency == CUR_LUNA and sent_currency.upper() == "BLUNA":
        # Special case: instant unbond (looks like swap)
        return make_unbond_instant_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)

    return _make_tx_exchange(
        txinfo, sent_amount, sent_currency, received_amount, received_currency, TX_TYPE_TRADE, txid, empty_fee)


def make_staking_tx(txinfo, reward_amount, reward_currency, txid=None, empty_fee=False, z_index=0):
    return _make_tx_received(txinfo, reward_amount, reward_currency, TX_TYPE_STAKING, txid, empty_fee, z_index=z_index)


def make_bond_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx_exchange(txinfo, sent_amount, sent_currency, received_amount, received_currency, TX_TYPE_BOND)


def make_unbond_tx(txinfo):
    return make_simple_tx(txinfo, TX_TYPE_UNBOND)


def make_unbond_instant_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx_exchange(txinfo, sent_amount, sent_currency, received_amount, received_currency, TX_TYPE_UNBOND_INSTANT)


def make_unbond_withdraw_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx_exchange(txinfo, sent_amount, sent_currency, received_amount, received_currency, TX_TYPE_UNBOND_WITHDRAW)


def make_anchor_earn_deposit_tx(txinfo, amount_ust, amount_aust, empty_fee=False, z_index=0):
    txinfo.comment = "earn_deposit"
    return _make_tx_exchange(txinfo, amount_ust, CUR_UST, amount_aust, CUR_AUST, TX_TYPE_EARN_DEPOSIT, empty_fee=empty_fee, z_index=z_index)


def make_anchor_earn_withdraw_tx(txinfo, amount_ust, amount_aust, empty_fee=False, z_index=0):
    txinfo.comment = "earn_withdraw"
    return _make_tx_exchange(txinfo, amount_aust, CUR_AUST, amount_ust, CUR_UST, TX_TYPE_EARN_WITHDRAW, empty_fee=empty_fee, z_index=z_index)


def make_anchor_earn_interest_tx(txinfo, interest_amount, interest_currency, empty_fee=False, z_index=0):
    txinfo.comment = "earn_interest"
    return make_staking_tx(txinfo, interest_amount, interest_currency, empty_fee=empty_fee, z_index=z_index)


def make_airdrop_tx(txinfo, reward_amount, reward_currency, txid=None, empty_fee=False):
    return _make_tx_received(txinfo, reward_amount, reward_currency, TX_TYPE_AIRDROP, txid, empty_fee=empty_fee)


def make_transfer_out_tx(txinfo, sent_amount, sent_currency):
    return _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_TRANSFER)


def make_transfer_in_tx(txinfo, received_amount, received_currency):
    return _make_tx_received(txinfo, received_amount, received_currency, TX_TYPE_TRANSFER)


def make_lp_deposit_tx(txinfo, sent_amount, sent_currency, lp_amount, lp_currency, txid=None, empty_fee=False, z_index=0):
    return _make_tx_exchange(
        txinfo, sent_amount, sent_currency, lp_amount, lp_currency, TX_TYPE_LP_DEPOSIT, txid, empty_fee, z_index=z_index)


def make_lp_withdraw_tx(txinfo, lp_amount, lp_currency, received_amount, received_currency, txid=None, empty_fee=False):
    return _make_tx_exchange(
        txinfo, lp_amount, lp_currency, received_amount, received_currency, TX_TYPE_LP_WITHDRAW, txid, empty_fee)


def make_lp_stake_tx(txinfo, lp_amount, lp_currency, empty_fee=False, z_index=0):
    return _make_tx_sent(txinfo, lp_amount, lp_currency, TX_TYPE_LP_STAKE, empty_fee=empty_fee, z_index=z_index)


def make_lp_unstake_tx(txinfo, lp_amount, lp_currency):
    return _make_tx_received(txinfo, lp_amount, lp_currency, TX_TYPE_LP_UNSTAKE)


def make_deposit_collateral_tx(txinfo, sent_amount, sent_currency, z_index=0):
    return _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_DEPOSIT_COLLATERAL, z_index=z_index)


def make_withdraw_collateral_tx(txinfo, received_amount, received_currency, empty_fee=False, z_index=0):
    return _make_tx_received(
        txinfo, received_amount, received_currency, TX_TYPE_WITHDRAW_COLLATERAL, empty_fee=empty_fee, z_index=z_index)


def make_borrow_tx(txinfo, received_amount, received_currency, empty_fee=False, z_index=0):
    txinfo.comment = "borrow " + txinfo.comment
    return _make_tx_received(
        txinfo, received_amount, received_currency, TX_TYPE_BORROW, empty_fee=empty_fee, z_index=z_index)


def make_repay_tx(txinfo, sent_amount, sent_currency, z_index=0):
    txinfo.comment = "repay " + txinfo.comment
    return _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_REPAY, z_index=z_index)


def make_gov_stake_tx(txinfo, sent_amount, sent_currency):
    row = _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_GOV_STAKE)
    return row


def make_gov_unstake_tx(txinfo, received_amount, received_currency):
    txinfo.comment += "Need manual stake rewards calculation for {}.".format(received_currency)
    row = _make_tx_received(txinfo, received_amount, received_currency, TX_TYPE_GOV_UNSTAKE)
    return row


def make_nft_reserve_tx(txinfo, sent_amount, sent_currency, name=""):
    txinfo.comment = _mint_comment(name)
    row = _make_tx_exchange(txinfo, sent_amount, sent_currency, 1, "unknown", TX_TYPE_NFT_MINT)
    return row


def make_nft_mint_no_purchase_tx(txinfo, nft_currency, name=""):
    txinfo.comment = _mint_comment(name)
    row = _make_tx_received(txinfo, 1, nft_currency, TX_TYPE_NFT_MINT)
    return row


def make_nft_mint_tx(txinfo, sent_amount, sent_currency, received_currency, name=""):
    txinfo.comment = _mint_comment(name)
    row = _make_tx_exchange(txinfo, sent_amount, sent_currency, 1, received_currency, TX_TYPE_TRADE)
    return row


def make_nft_transfer_out_tx(txinfo, sent_currency, name=""):
    txinfo.comment = _nft_comment(name)
    return _make_tx_sent(txinfo, 1, sent_currency, TX_TYPE_TRANSFER)


def make_nft_transfer_in_tx(txinfo, received_currency, name=""):
    txinfo.comment = _nft_comment(name)
    return _make_tx_received(txinfo, 1, received_currency, TX_TYPE_TRANSFER)


def make_nft_offer_sell_tx(txinfo, sent_currency, offer_amount, offer_currency, name=""):
    txinfo.comment = "nft {}, offer sell {} {}".format(name, offer_amount, offer_currency)
    return _make_tx_sent(txinfo, 1, sent_currency, TX_TYPE_NFT_OFFER_SELL)


def make_nft_buy_tx(txinfo, sent_amount, sent_currency, received_currency, name=""):
    txinfo.comment = _nft_comment(name)
    return _make_tx_exchange(txinfo, sent_amount, sent_currency, 1, received_currency, TX_TYPE_TRADE)


def make_nft_withdraw(txinfo, received_amount, received_currency):
    txinfo.comment = "MUST MANUALLY DEDUCE NFT SALES (if exists)"
    return _make_tx_received(txinfo, received_amount, received_currency, TX_TYPE_NFT_WITHDRAW)


def make_nft_deposit(txinfo, sent_amount, sent_currency):
    txinfo.comment = "deposit for nft mint"
    return _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_NFT_DEPOSIT)


def _mint_comment(name):
    result = "mint"
    if name:
        result += " {}".format(name)
    return result


def _nft_comment(name):
    result = "nft"
    if name:
        result += " {}".format(name)
    return result
