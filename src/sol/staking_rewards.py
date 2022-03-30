import csv
import glob
import logging
import os
import subprocess

from sol.api_rpc import RpcAPI
from sol.config_sol import localconfig
from sol.make_tx import make_sol_reward_tx

DATADIR = os.path.dirname(os.path.realpath(__file__)) + "/data_staking_rewards"
START_EPOCH = 132  # epoch of first ever staking reward


def reward_txs(wallet_info, exporter, progress):
    """Get reward transactions across all staking addresses for this wallet"""
    staking_addresses = wallet_info.get_staking_addresses()
    wallet_address = wallet_info.wallet_address

    for i, addr in enumerate(staking_addresses):
        progress.report(i, f"Fetching rewards for {addr}...", "staking")
        _reward_txs(wallet_address, exporter, addr)


def _reward_txs(wallet_address, exporter, staking_address):
    """Get reward transactions for this staking address"""
    latest_epoch = RpcAPI.get_latest_epoch()

    rewards = []

    for epoch in range(START_EPOCH, latest_epoch):
        timestamp, reward = _get_reward(epoch, staking_address)
        if not reward:
            continue
        rewards.append([epoch, timestamp, reward])

    for epoch, timestamp, reward in rewards:
        txid = f"{staking_address}.{epoch}"
        row = make_sol_reward_tx(timestamp, reward, wallet_address, txid)
        exporter.ingest_row(row)


def _get_reward(epoch, staking_address):
    """ Returns single reward (timestamp_of_reward, float_reward_amount) for staking_address at this epoch. """
    flush = localconfig.job is None

    epoch_file_path = EpochFile.path(epoch)
    if epoch_file_path:
        # Found epoch rewards file.  Find user's reward in this epoch.

        slot = EpochFile.slot(epoch_file_path)
        amount = EpochFile.read_rewards(staking_address, epoch_file_path)
        if amount is None:
            return None, None
    else:
        logging.info("Fetching inflation reward for staking_address=%s, epoch=%s ...", staking_address, epoch)
        amount, slot = RpcAPI.get_inflation_reward(staking_address, epoch)

        if flush and slot:
            logging.info("Retrieving rewards for all users in epoch=%s...", epoch)
            block_rewards = RpcAPI.get_block_rewards(slot)
            if not block_rewards:
                return None, None
            EpochFile.write_rewards(epoch, slot, block_rewards)

    # Get timestamp of the reward
    if not amount or not slot:
        return None, None
    timestamp = _block_datetime(slot)

    return timestamp, amount


def _cmd2(s):
    return subprocess.getoutput(s)


def _block_datetime(block):
    block = str(block)

    if block in localconfig.blocks:
        return localconfig.blocks[block]

    logging.info("Fetching block time for block=%s", block)
    timestamp = RpcAPI.get_block_time(block)
    localconfig.blocks[block] = timestamp
    return timestamp


class EpochFile:
    # epoch.<epoch>.<date>.<slot>.csv

    @classmethod
    def _epoch_path(cls, epoch, date, slot):
        return "{}/epoch.{}.{}.{}.csv".format(DATADIR, epoch, date, slot)

    @classmethod
    def path(cls, epoch):
        """ Returns path of epoch file if exists, else None """
        glob_expr = "{}/epoch.{}.*.csv".format(DATADIR, epoch)
        result = glob.glob(glob_expr)
        if result and len(result) == 1:
            mypath = result[0]
            return mypath
        else:
            return None

    @classmethod
    def slot(cls, path):
        filename = os.path.basename(path)
        _, epoch, date, slot, _ = filename.split(".")
        return slot

    @classmethod
    def read_rewards(cls, staking_address, path):
        result = _cmd2(f"grep {staking_address} {path}")
        if not result:
            return None
        _, amount = result.split(",")
        return amount

    @classmethod
    def write_rewards(cls, epoch, slot, block_rewards):
        """ Writes rewards for all users in this epoch to a csv file """
        # Determine path for epoch file
        dt = _block_datetime(slot)
        date = dt.split(" ")[0]
        path = cls._epoch_path(epoch, date, slot)

        with open(path, "w") as f:
            mywriter = csv.writer(f)

            mywriter.writerows(block_rewards)
        logging.info("Wrote to %s", path)
