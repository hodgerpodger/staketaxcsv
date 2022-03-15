import logging

from common.make_tx import make_reward_tx, make_spend_tx
from terra import util_terra
from terra.config_terra import localconfig
from terra.constants import CUR_KRT, CUR_LUNA, CUR_UST

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

    # Create row for spend fee
    row = make_spend_tx(txinfo, txinfo.fee, txinfo.fee_currency)
    row.fee, row.fee_currency = "", ""
    row.z_index = -1
    if msgtype == "staking/MsgDelegate":
        row.comment = "fee for delegate"
    elif msgtype == "distribution/MsgWithdrawDelegationReward":
        row.comment = "fee for withdraw_delegate_reward"
    elif msgtype == "staking/MsgBeginRedelegate":
        row.comment = "fee for redelegate"
    elif msgtype == "staking/MsgUndelegate":
        row.comment = "fee for undelegate"
    else:
        logging.error("handle_reward(): unhandled msgtype=%s", msgtype)
    exporter.ingest_row(row)
