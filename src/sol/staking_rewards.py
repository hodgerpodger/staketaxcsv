
import csv
import logging
import os
import subprocess
from sol.api_rpc import RpcAPI
from sol.make_tx import make_sol_reward_tx
from sol.config_sol import localconfig

DATADIR = os.path.dirname(os.path.realpath(__file__)) + "/data_staking_rewards"


def reward_txs(wallet_info, exporter, progress):
    """ Get reward transactions across all staking addresses for this wallet """
    staking_addresses = wallet_info.get_staking_addresses()
    wallet_address = wallet_info.wallet_address

    for i, addr in enumerate(staking_addresses):
        progress.report("staking", i, "Fetching rewards for {}...".format(addr))
        _reward_txs(wallet_address, exporter, addr)


def _reward_txs(wallet_address, exporter, staking_address):
    """ Get reward transactions for this staking address """
    start_epoch = 132  # epoch of first staking reward ever
    latest_epoch = RpcAPI.get_latest_epoch()

    rewards = []
    for epoch in range(start_epoch, latest_epoch):
        timestamp, reward = _get_reward(epoch, staking_address)
        if not reward:
            continue
        rewards.append([epoch, timestamp, reward])

    for epoch, timestamp, reward in rewards:
        txid = "{}.{}".format(staking_address, epoch)
        row = make_sol_reward_tx(timestamp, reward, wallet_address, txid)
        exporter.ingest_row(row)


def _get_reward(epoch, staking_address):
    """ Returns single reward (timestamp_of_reward, float_reward_amount) for staking_address at this epoch. """
    flush = (localconfig.job is None)

    filename = "{}/{}.csv".format(DATADIR, epoch)
    if os.path.exists(filename):
        # Reward data in file.  Extract reward.
        result = _cmd2("head -n 1 {}".format(filename))
        _, slot = result.split(",")

        result = _cmd2("grep {} {}".format(staking_address, filename))
        if not result:
            return None, None
        _, amount = result.split(",")
    else:
        # At epoch, fetch reward data for staking address
        logging.info("Fetching inflation reward for staking_address=%s, epoch=%s ...", staking_address, epoch)
        amount, slot = RpcAPI.get_inflation_reward(staking_address, epoch)

        if flush and slot:
            # At epoch, fetch reward data for all users and save to file
            logging.info("Retrieving and flushing rewards to file for epoch=%s...", epoch)
            block_rewards = RpcAPI.get_block_rewards(slot)
            if not block_rewards:
                return None, None
            with open(filename, 'w') as f:
                mywriter = csv.writer(f)
                mywriter.writerow(["slot", slot])
                mywriter.writerows(block_rewards)
            logging.info("Wrote to %s", filename)

    if not amount or not slot:
        return None, None
    ts = _get_timestamp(slot)
    return ts, amount


def _cmd2(s):
    return subprocess.getoutput(s)


def _get_timestamp(block):
    block = str(block)

    if block in localconfig.blocks:
        return localconfig.blocks[block]

    logging.info("Fetching block time for block=%s", block)
    ts = RpcAPI.get_block_time(block)
    localconfig.blocks[block] = ts
    return ts
