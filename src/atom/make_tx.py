from atom.constants import CUR_ATOM
from common.make_tx import make_reward_tx, make_transfer_in_tx, make_transfer_out_tx


def make_transfer_receive_tx(txinfo, received_amount, received_currency=None):
    if not received_currency:
        received_currency = CUR_ATOM if txinfo.fee else ""

    return make_transfer_in_tx(txinfo, received_amount, received_currency)


def make_transfer_send_tx(txinfo, sent_amount, sent_currency=None):
    if not sent_currency:
        sent_currency = CUR_ATOM if txinfo.fee else ""

    return make_transfer_out_tx(txinfo, sent_amount, sent_currency, None)


def make_atom_reward_tx(txinfo, reward_amount):
    return make_reward_tx(txinfo, reward_amount, CUR_ATOM)
