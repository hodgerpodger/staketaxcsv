
from osmo.make_tx import make_osmo_reward_tx, make_osmo_simple_tx
import osmo.constants as co
from common.Exporter import (
TX_TYPE_STAKING_REDELEGATE, TX_TYPE_STAKING_DELEGATE, TX_TYPE_STAKING_UNDELEGATE,
    TX_TYPE_OSMO_WITHDRAW_DELEGATOR_REWARD, TX_TYPE_OSMO_WITHDRAW_COMMISSION
)
from osmo.RewardWallet import RewardWallet
from osmo import util_osmo


TX_TYPES_DELEGATION = {
    co.MSG_TYPE_REDELEGATE: TX_TYPE_STAKING_REDELEGATE,
    co.MSG_TYPE_DELEGATE: TX_TYPE_STAKING_DELEGATE,
    co.MSG_TYPE_UNDELEGATE: TX_TYPE_STAKING_UNDELEGATE,
    co.MSG_TYPE_WITHDRAW_REWARD : TX_TYPE_OSMO_WITHDRAW_DELEGATOR_REWARD,
    co.MSG_TYPE_WITHDRAW_COMMISSION : TX_TYPE_OSMO_WITHDRAW_COMMISSION
}


def handle_staking(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    message = msginfo.message
    wallet_address = txinfo.wallet_address

    # Include reward wallet inbound transfers in addition to wallet inbound transfers
    reward_wallet = RewardWallet.get(wallet_address)
    if reward_wallet and reward_wallet != wallet_address:
        reward_transfers_in, _ = util_osmo._transfers(msginfo.log, reward_wallet)
        transfers_in.extend(reward_transfers_in)

    total = 0
    for amount, currency in transfers_in:
        total += amount

    if total > 0:
        row = make_osmo_reward_tx(txinfo, msginfo, total, currency)
        exporter.ingest_row(row)
    else:
        # No reward: add non-income delegation transaction just so transaction doesn't appear "missing"
        msg_type = message["@type"]
        tx_type = TX_TYPES_DELEGATION[msg_type]
        row = make_osmo_simple_tx(txinfo, msginfo, tx_type)
        exporter.ingest_row(row)
