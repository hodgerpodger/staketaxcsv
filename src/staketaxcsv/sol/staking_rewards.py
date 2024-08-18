import logging
from datetime import datetime

from staketaxcsv.sol.api_rpc import RpcAPI
from staketaxcsv.sol.make_tx import make_sol_reward_tx
from staketaxcsv.settings_csv import SOL_REWARDS_DB_READ
from staketaxcsv.sol.staking_rewards_common import get_epochs_all, epoch_slot_and_time
from staketaxcsv.sol.staking_rewards_db import StakingRewardsDB
from staketaxcsv.sol.api_marinade import MarinadeAPI
from staketaxcsv.sol.constants import BILLION


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

    # Add marinade native staking rewards separately
    _rewards_txs_marinade_native(wallet_info, exporter, start_date, end_date)


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

    amount = RpcAPI.get_inflation_reward(staking_address, epoch)
    if not amount:
        return None, None

    _, ts = epoch_slot_and_time(epoch)
    if not ts:
        return None, None

    return ts, amount


def _rewards_txs_marinade_native(wallet_info, exporter, start_date, end_date):
    if not wallet_info.has_marinade_native:
        return

    wallet_address = wallet_info.wallet_address

    # Query marinade native staking rewards (all time)
    rewards = []
    data = MarinadeAPI.native_staking_rewards(wallet_address)
    for points in data["data_points"]:
        epoch = points["epoch"]                          # i.e. 542
        inflation_rewards = points["inflation_rewards"]  # i.e. 882019919",
        created_at = points["created_at"]                # i.e. "2023-12-10T01:17:22Z"

        ts = created_at.replace('T', ' ').replace('Z', '')
        amount_sol = float(inflation_rewards) / BILLION
        rewards.append((epoch, ts, amount_sol))

    rewards = _filter_date(rewards, start_date, end_date)

    # Add to exporter
    for epoch, ts, amount in rewards:
        txid = f"marinade_native_epoch.{epoch}"
        row = make_sol_reward_tx(ts, amount, wallet_address, txid)
        exporter.ingest_row(row)
