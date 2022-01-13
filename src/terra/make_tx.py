from common.ExporterTypes import (
    TX_TYPE_BOND,
    TX_TYPE_DEPOSIT_COLLATERAL,
    TX_TYPE_GOV_STAKE,
    TX_TYPE_GOV_UNSTAKE,
    TX_TYPE_LP_DEPOSIT,
    TX_TYPE_LP_STAKE,
    TX_TYPE_LP_UNSTAKE,
    TX_TYPE_LP_WITHDRAW,
    TX_TYPE_NFT_DEPOSIT,
    TX_TYPE_NFT_MINT,
    TX_TYPE_NFT_OFFER_SELL,
    TX_TYPE_NFT_WITHDRAW,
    TX_TYPE_TRADE,
    TX_TYPE_TRANSFER,
    TX_TYPE_UNBOND,
    TX_TYPE_UNBOND_INSTANT,
    TX_TYPE_UNBOND_WITHDRAW,
    TX_TYPE_WITHDRAW_COLLATERAL,
)
from common.make_tx import _make_tx_exchange, _make_tx_received, _make_tx_sent, make_simple_tx
from terra.constants import CUR_LUNA


def make_swap_tx_terra(txinfo, sent_amount, sent_currency, received_amount, received_currency,
                       txid=None, empty_fee=False):
    return _make_tx_exchange(
        txinfo, sent_amount, sent_currency, received_amount, received_currency, TX_TYPE_TRADE, txid, empty_fee)


def make_bond_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx_exchange(txinfo, sent_amount, sent_currency, received_amount, received_currency, TX_TYPE_BOND)


def make_unbond_tx(txinfo):
    return make_simple_tx(txinfo, TX_TYPE_UNBOND)


def make_unbond_instant_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx_exchange(txinfo, sent_amount, sent_currency, received_amount, received_currency,
                             TX_TYPE_UNBOND_INSTANT)


def make_unbond_withdraw_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency):
    return _make_tx_exchange(txinfo, sent_amount, sent_currency, received_amount, received_currency,
                             TX_TYPE_UNBOND_WITHDRAW)


def make_lp_deposit_tx(txinfo, sent_amount, sent_currency, lp_amount, lp_currency, txid=None, empty_fee=False,
                       z_index=0):
    # Default is _LP_DEPOSIT.  If optional parameter lp set, treat as trade.
    # tx_type = TX_TYPE_TRADE if localconfig.lp else TX_TYPE_LP_DEPOSIT
    return _make_tx_exchange(
        txinfo, sent_amount, sent_currency, lp_amount, lp_currency, TX_TYPE_LP_DEPOSIT, txid, empty_fee,
        z_index=z_index)


def make_lp_withdraw_tx(txinfo, lp_amount, lp_currency, received_amount, received_currency, txid=None,
                        empty_fee=False):
    # Default is _LP_WITHDRAW.  If optional parameter lp set, treat as trade.
    # tx_type = TX_TYPE_TRADE if localconfig.lp else TX_TYPE_LP_WITHDRAW
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


def make_gov_stake_tx(txinfo, sent_amount, sent_currency):
    row = _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_GOV_STAKE)
    return row


def make_gov_unstake_tx(txinfo, received_amount, received_currency):
    txinfo.comment += "Need manual stake rewards calculation for {}.".format(received_currency)
    row = _make_tx_received(txinfo, received_amount, received_currency, TX_TYPE_GOV_UNSTAKE)
    return row


def make_nft_reserve_tx(txinfo, sent_amount, sent_currency, name=""):
    row = _make_tx_exchange(txinfo, sent_amount, sent_currency, 1, "unknown", TX_TYPE_NFT_MINT)
    row.comment = _mint_comment(name)
    return row


def make_nft_mint_no_purchase_tx(txinfo, nft_currency, name=""):
    row = _make_tx_received(txinfo, 1, nft_currency, TX_TYPE_NFT_MINT)
    row.comment = _mint_comment(name)
    return row


def make_nft_mint_tx(txinfo, sent_amount, sent_currency, received_currency, name=""):
    row = _make_tx_exchange(txinfo, sent_amount, sent_currency, 1, received_currency, TX_TYPE_TRADE)
    row.comment = _mint_comment(name)
    return row


def make_nft_transfer_out_tx(txinfo, sent_currency, name=""):
    row = _make_tx_sent(txinfo, 1, sent_currency, TX_TYPE_TRANSFER)
    row.comment = _nft_comment(name)
    return row


def make_nft_transfer_in_tx(txinfo, received_currency, name=""):
    row = _make_tx_received(txinfo, 1, received_currency, TX_TYPE_TRANSFER)
    row.comment = _nft_comment(name)
    return row


def make_nft_offer_sell_tx(txinfo, sent_currency, offer_amount, offer_currency, name=""):
    row = _make_tx_sent(txinfo, 1, sent_currency, TX_TYPE_NFT_OFFER_SELL)
    row.comment = "nft {}, offer sell {} {}".format(name, offer_amount, offer_currency)
    return row


def make_nft_buy_tx(txinfo, sent_amount, sent_currency, received_currency, name=""):
    row = _make_tx_exchange(txinfo, sent_amount, sent_currency, 1, received_currency, TX_TYPE_TRADE)
    row.comment = _nft_comment(name)
    return row


def make_nft_withdraw(txinfo, received_amount, received_currency):
    row = _make_tx_received(txinfo, received_amount, received_currency, TX_TYPE_NFT_WITHDRAW)
    row.comment = "MUST MANUALLY DEDUCE NFT SALES (if exists)"
    return row


def make_nft_deposit(txinfo, sent_amount, sent_currency):
    row = _make_tx_sent(txinfo, sent_amount, sent_currency, TX_TYPE_NFT_DEPOSIT)
    row.comment = "deposit for nft mint"
    return row


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
