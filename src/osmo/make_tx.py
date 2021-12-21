

from common.Exporter import TX_TYPE_STAKING_DELEGATE, TX_TYPE_STAKING
from common.make_tx import make_simple_tx


def make_delegate_tx(txinfo, amount, currency):
    row = make_simple_tx(txinfo, TX_TYPE_STAKING_DELEGATE)
    row.comment = "delegated {} {}".format(amount, currency)
    return row
