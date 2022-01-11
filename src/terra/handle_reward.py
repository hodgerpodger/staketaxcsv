import logging

from common.ExporterTypes import (
    TX_TYPE_STAKING_DELEGATE,
    TX_TYPE_STAKING_REDELEGATE,
    TX_TYPE_STAKING_UNDELEGATE,
    TX_TYPE_STAKING_WITHDRAW_REWARD,
)
from common.make_tx import make_reward_tx
from terra import util_terra
from terra.config_terra import localconfig
from terra.constants import CUR_KRT, CUR_LUNA, CUR_UST
from terra.handle_simple import handle_simple

REWARD_CURRENCIES = set([
    CUR_LUNA,
    CUR_UST,
    CUR_KRT
])


def handle_reward(exporter, elem, txinfo, msgtype):
    """ Returns reward amount of (luna, ust, krt) for this transaction """
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid, multicurrency=True)

    # Create separate row for action
    if msgtype == "staking/MsgDelegate":
        handle_simple(exporter, txinfo, TX_TYPE_STAKING_DELEGATE, z_index=-1)
    elif msgtype == "distribution/MsgWithdrawDelegationReward":
        handle_simple(exporter, txinfo, TX_TYPE_STAKING_WITHDRAW_REWARD, z_index=-1)
    elif msgtype == "staking/MsgBeginRedelegate":
        handle_simple(exporter, txinfo, TX_TYPE_STAKING_REDELEGATE, z_index=-1)
    elif msgtype == "staking/MsgUndelegate":
        handle_simple(exporter, txinfo, TX_TYPE_STAKING_UNDELEGATE, z_index=-1)
    else:
        logging.error("handle_reward(): unhandled msgtype=%s", msgtype)

    # Sum rewards by currency (may have multiple multiple messages within same transaction)
    rewards = {}
    for amount, currency in transfers_in:
        rewards[currency] = rewards.get(currency, 0) + float(amount)

    # Create rows for staking rewards
    i = 0
    for currency in sorted(rewards.keys()):
        # Skip minor currencies if option set
        if not localconfig.minor_rewards and currency not in REWARD_CURRENCIES:
            continue

        amount = rewards[currency]
        if amount == 0:
            logging.info("Skipping reward=0 for currency=%s", currency)
            continue

        row = make_reward_tx(txinfo, amount, currency, txid, empty_fee=True)
        exporter.ingest_row(row)
        i += 1
