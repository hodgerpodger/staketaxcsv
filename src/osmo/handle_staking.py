import osmo.constants as co
from common.ExporterTypes import (
    TX_TYPE_OSMO_WITHDRAW_COMMISSION,
    TX_TYPE_OSMO_WITHDRAW_DELEGATOR_REWARD,
    TX_TYPE_STAKING_DELEGATE,
    TX_TYPE_STAKING_REDELEGATE,
    TX_TYPE_STAKING_UNDELEGATE,
)
from osmo.make_tx import make_osmo_reward_tx, make_osmo_simple_tx

TX_TYPES_DELEGATION = {
    co.MSG_TYPE_REDELEGATE: TX_TYPE_STAKING_REDELEGATE,
    co.MSG_TYPE_DELEGATE: TX_TYPE_STAKING_DELEGATE,
    co.MSG_TYPE_UNDELEGATE: TX_TYPE_STAKING_UNDELEGATE,
    co.MSG_TYPE_WITHDRAW_REWARD: TX_TYPE_OSMO_WITHDRAW_DELEGATOR_REWARD,
    co.MSG_TYPE_WITHDRAW_COMMISSION: TX_TYPE_OSMO_WITHDRAW_COMMISSION
}


def handle_staking(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    total = 0
    for amount, currency in transfers_in:
        total += amount

    if total > 0:
        row = make_osmo_reward_tx(txinfo, msginfo, total, currency)
        exporter.ingest_row(row)
    else:
        # No reward: add non-income delegation transaction just so transaction doesn't appear "missing"
        row = make_osmo_simple_tx(txinfo, msginfo)
        exporter.ingest_row(row)
