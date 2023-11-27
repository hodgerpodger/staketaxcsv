import logging
from datetime import datetime

from staketaxcsv.sol.api_rpc import RpcAPI
from staketaxcsv.sol.make_tx import make_sol_reward_tx
from staketaxcsv.settings_csv import SOL_REWARDS_DB_READ
from staketaxcsv.sol.staking_rewards_common import slot_to_timestamp, get_epochs_all
from staketaxcsv.sol.staking_rewards_db import StakingRewardsDB


def reward_txs(wallet_info, exporter, progress, min_date):
    """Get reward transactions across all staking addresses for this wallet"""
    staking_addresses = wallet_info.get_staking_addresses()
    wallet_address = wallet_info.wallet_address

    for i, staking_address in enumerate(staking_addresses):
        progress.report(i, f"Fetching rewards for {staking_address}...", "staking")
        result = _rewards(staking_address, min_date)

        for epoch, timestamp, reward in result:
            txid = f"{staking_address}.{epoch}"
            row = make_sol_reward_tx(timestamp, reward, wallet_address, txid)
            exporter.ingest_row(row)


def date_to_dt(ymd):
    return datetime.strptime(ymd, "%Y-%m-%d")


def _rewards(staking_address, min_date):
    """ Get reward transactions for this staking_address within epochs list """
    out = []
    epochs_all = get_epochs_all()

    if SOL_REWARDS_DB_READ is False:
        # No DB available.  Query RPC for all rewards info.
        logging.info("No db available.  Using Solana RPC only to get rewards.  This will take a while ...")
        for epoch in epochs_all:
            ts, amount = _lookup_reward_via_rpc(staking_address, epoch)
            if ts and amount:
                out.append((epoch, ts, amount))
        return out

    rewards_db = StakingRewardsDB().get_rewards_for_address(staking_address, epochs_all)
    logging.info("Found rewards_db: %s", rewards_db)

    for epoch in epochs_all:
        if epoch in rewards_db:
            ts, amount = rewards_db[epoch]
            if float(amount) > 0:
                out.append((epoch, ts, amount))
        else:
            ts, amount = _lookup_reward_via_rpc(staking_address, epoch)
            if ts and amount:
                out.append((epoch, ts, amount))

    if min_date:
        # Filter out staking rewards before min_date
        out2 = []
        for epoch, ts, amount in out:
            date, _ = ts.split()
            if date_to_dt(date) >= date_to_dt(min_date):
                out2.append((epoch, ts, amount))
        return out2
    else:
        return out


def _lookup_reward_via_rpc(staking_address, epoch):
    logging.info("Querying RPC for rewards epoch=%s staking_address=%s ...", epoch, staking_address)
    amount, slot = RpcAPI.get_inflation_reward(staking_address, epoch)
    if amount and slot:
        ts = slot_to_timestamp(slot)
        return ts, amount
    else:
        return None, None
