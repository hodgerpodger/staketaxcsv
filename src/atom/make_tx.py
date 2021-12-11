
from common.Exporter import (TX_TYPE_STAKING)
from common.make_tx import _make_tx_received, make_transfer_out_tx, make_transfer_in_tx
from atom.constants import CUR_ATOM


def make_reward_tx(txinfo, reward):
    return _make_tx_received(txinfo, reward, CUR_ATOM, TX_TYPE_STAKING)


def make_transfer_receive_tx(txinfo, received_amount, received_currency=None):
    if not received_currency:
        received_currency = CUR_ATOM if txinfo.fee else ""

    return make_transfer_in_tx(txinfo, received_amount, received_currency)


def make_transfer_send_tx(txinfo, sent_amount, sent_currency=None):
    if not sent_currency:
        sent_currency = CUR_ATOM if txinfo.fee else ""

    return make_transfer_out_tx(txinfo, sent_amount, sent_currency, None)
