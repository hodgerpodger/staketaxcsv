import logging
from datetime import datetime

from staketaxcsv.sol.api_rpc import RpcAPI
from staketaxcsv.sol.make_tx import make_sol_reward_tx
from staketaxcsv.settings_csv import SOL_REWARDS_DB_READ
from staketaxcsv.sol.staking_rewards_common import slot_to_timestamp, get_epochs_all
from staketaxcsv.sol.staking_rewards_db import StakingRewardsDB


def reward_txs(wallet_info, exporter, progress, start_date=None, end_date=None):
    """Get reward transactions across all staking addresses for this wallet"""
    staking_addresses = wallet_info.get_staking_addresses()
    wallet_address = wallet_info.wallet_address

    for i, staking_address in enumerate(staking_addresses):
        progress.report(i, f"Fetching rewards for {staking_address}...", "staking")
        result = _rewards(staking_address, start_date, end_date)

        for epoch, timestamp, reward in result:
            txid = f"{staking_address}.{epoch}"
            row = make_sol_reward_tx(timestamp, reward, wallet_address, txid)
            exporter.ingest_row(row)


def _rewards(staking_address, start_date=None, end_date=None):
    list_rewards = _rewards_all_time(staking_address)
    return _filter_date(list_rewards, start_date, end_date)


def _rewards_all_time(staking_address):
    """ Get reward transactions for this staking_address within epochs list """
    epochs_all = get_epochs_all()

    if SOL_REWARDS_DB_READ is False:
        # No DB available.  Query RPC for all rewards info.
        logging.info("No db available.  Using Solana RPC only to get rewards.  This will take a while ...")

        out = []
        for epoch in epochs_all:
            ts, amount = _lookup_reward_via_rpc(staking_address, epoch)
            if ts and amount:
                out.append((epoch, ts, amount))
        return out

    rewards_db = StakingRewardsDB().get_rewards_for_address(staking_address, epochs_all)
    logging.info("Found rewards_db: %s", rewards_db)

    out = []
    for epoch in epochs_all:
        # Get reward for this epoch

        if epoch in rewards_db:
            # using db data
            ts, amount = rewards_db[epoch]
            if float(amount) > 0:
                out.append((epoch, ts, amount))
        else:
            # using rpc call
            ts, amount = _lookup_reward_via_rpc(staking_address, epoch)
            if ts and amount:
                out.append((epoch, ts, amount))

    return out


def _filter_date(rewards, start_date=None, end_date=None):
    """ Filter result within date range (if specified) """
    out = []

    for epoch, ts, amount in rewards:
        date, _ = ts.split()
        if (
            (start_date is None or _date_to_dt(date) >= _date_to_dt(start_date))
            and (end_date is None or _date_to_dt(date) <= _date_to_dt(end_date))
        ):
            out.append((epoch, ts, amount))

    return out


def _date_to_dt(ymd):
    return datetime.strptime(ymd, "%Y-%m-%d")


def _lookup_reward_via_rpc(staking_address, epoch):
    logging.info("Querying RPC for rewards epoch=%s staking_address=%s ...", epoch, staking_address)
    amount, slot = RpcAPI.get_inflation_reward(staking_address, epoch)
    if amount and slot:
        ts = slot_to_timestamp(slot)
        return ts, amount
    else:
        return None, None
