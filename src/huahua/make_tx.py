from huahua.constants import CUR_HUAHUA
from common.make_tx import make_reward_tx, make_transfer_in_tx, make_transfer_out_tx


def make_transfer_receive_tx(txinfo, received_amount, received_currency=None):
    if not received_currency:
        received_currency = CUR_HUAHUA if txinfo.fee else ""

    return make_transfer_in_tx(txinfo, received_amount, received_currency)


def make_transfer_send_tx(txinfo, sent_amount, sent_currency=None):
    if not sent_currency:
        sent_currency = CUR_HUAHUA if txinfo.fee else ""

    return make_transfer_out_tx(txinfo, sent_amount, sent_currency, None)


def make_huahua_reward_tx(txinfo, reward_amount):
    return make_reward_tx(txinfo, reward_amount, CUR_HUAHUA)
