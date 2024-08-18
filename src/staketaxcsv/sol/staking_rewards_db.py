"""
usage: python3 staketaxcsv/sol/staking_rewards_db.py

  * Writes all staking rewards for all users for all time (that doesn't exist in db) to dynamodb database.

"""

import boto3
import logging
import random
import time
from concurrent.futures import as_completed, ThreadPoolExecutor
from botocore.exceptions import ClientError

from staketaxcsv.sol.staking_rewards_common import START_EPOCH, epoch_slot_and_time
from staketaxcsv.sol.api_rpc import RpcAPI

TABLE_STAKING_REWARDS = "staking_rewards"
FIELD_EPOCH_TIMESTAMPS = "_epoch_timestamps"
FIELD_PREFIX_ADDRESS = "addr_"
REFERENCE_ADDRESS_WITH_ALL_EPOCH_REWARDS = "8Vv2xVWSQtHji1Xf7Vj1vHKTa4em7zv7cAET96Vm2qt8"
BATCH_SIZE_READ = 100   # Should match batch size read items limit for dynamodb
TASK_SIZE_WRITE = 100   # Note: this is task write items size (not batch write items limit for dynamodb, which is 25)
MAX_WORKERS = 32
N_BLOCKS = 10


def rewards_all_users_write_db():
    """ Write/ensure all rewards for all users for all time to db. """
    db = StakingRewardsDB()

    # Find [start, end] epochs for rewards not in db yet.
    end_epoch = RpcAPI.get_latest_epoch()
    prev_end_epoch = _max_epoch_db(db)
    start_epoch = START_EPOCH if prev_end_epoch is None else prev_end_epoch + 1
    epochs = list(range(start_epoch, end_epoch))
    logging.info("epochs: %s", epochs)

    for x in range(start_epoch, end_epoch, N_BLOCKS):
        # Process 10 epochs at a time (lessens db writes/reads)
        cur_epochs = list(range(x, min(x + N_BLOCKS, end_epoch)))
        logging.info("cur_epochs: %s", cur_epochs)

        list_block_rewards = []
        for epoch in cur_epochs:
            reward_slot, ts = epoch_slot_and_time(epoch)

            # Retrieve rewards for all users in this epoch
            logging.info("Retrieving block rewards for epoch=%s, reward_slot=%s ...", epoch, reward_slot)
            block_rewards = RpcAPI.get_block_rewards(reward_slot)
            logging.info("Found len(block_rewards)=%s", len(block_rewards))
            time.sleep(30)  # throttled at times if too frequent

            list_block_rewards.append((epoch, reward_slot, ts, block_rewards))

        db.set_multi_block_rewards(list_block_rewards)


def _max_epoch_db(db):
    epoch_timestamps = db.get_epoch_timestamps()
    if len(epoch_timestamps) > 0:
        epochs = [int(x) for x in epoch_timestamps.keys()]
        return max(epochs)
    else:
        return None


class StakingRewardsDB:

    dynamodb = None
    table = None

    def __init__(self):
        if not StakingRewardsDB.dynamodb:
            StakingRewardsDB.dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
            StakingRewardsDB.table = StakingRewardsDB.dynamodb.Table(TABLE_STAKING_REWARDS)

    def _get(self, field_name):
        response = StakingRewardsDB.table.get_item(
            Key={'field': field_name}
        )

        if "Item" not in response:
            return None

        item = response['Item']
        data = item['data']
        return data

    def _set_overwrite(self, field_name, data):
        response = StakingRewardsDB.table.put_item(
            Item={
                'field': field_name,
                'data': data
            }
        )

    def set_epoch_timestamp(self, epoch, ts):
        epoch_timestamps = self._get(FIELD_EPOCH_TIMESTAMPS)
        if epoch_timestamps is None:
            epoch_timestamps = {}
        epoch_timestamps[str(epoch)] = ts

        self._set_overwrite(FIELD_EPOCH_TIMESTAMPS, epoch_timestamps)

    def get_epoch_timestamps(self):
        epoch_timestamps = self._get(FIELD_EPOCH_TIMESTAMPS)
        if epoch_timestamps is None:
            return {}
        else:
            return epoch_timestamps

    def set_multi_block_rewards(self, list_block_rewards):
        logging.info("set_multi_block_rewards() for epochs %s...", [x[0] for x in list_block_rewards])

        # Get existing reward data from db for addresses in block_rewards
        addrs = set()
        for epoch, slot, ts, block_rewards in list_block_rewards:
            for addr, amount in block_rewards:
                addrs.add(addr)
        rewards_db = self._db_read_rewards(list(addrs))

        # Update rewards_db with new block rewards
        for epoch, slot, ts, block_rewards in list_block_rewards:
            for addr, amount in block_rewards:
                rewards_db[addr][str(epoch)] = str(amount)

        # Send updates to db
        self._db_write_rewards(rewards_db)

        # Update slot_timestamps (which also marks completed data epochs in rewards db)
        for epoch, slot, ts, block_rewards in list_block_rewards:
            self.set_epoch_timestamp(epoch, ts)

    def _db_read_rewards(self, addrs):
        """ Gets existing reward data from db for list of addresses """
        logging.info("_db_read_rewards() starting for %s addresses ... ", len(addrs))

        # Run batch read requests in parallel using pool of threads.
        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks to pool
            futures = []
            for i in range(0, len(addrs), BATCH_SIZE_READ):
                future = executor.submit(self._batch_get, i, addrs)
                futures.append(future)
            logging.info("All tasks submitted.")

            # Log progress of tasks completed
            for f in as_completed(futures):
                results.append(f.result())

                num_read_items = len(results) * BATCH_SIZE_READ
                if num_read_items % 10000 == 0:
                    logging.info("%s of %s reads completed ... ", num_read_items, len(addrs))
            logging.info("All tasks completed.")

        # Combine results into single dictionary
        rewards_db = {}
        for result in results:
            for addr, addr_rewards in result.items():
                rewards_db[addr] = addr_rewards

        return rewards_db

    def _batch_get(self, i, addrs):
        """ Runs one batch read request """
        one_batch_addrs = addrs[i:i + BATCH_SIZE_READ]

        # Prepare batch read request
        k_list = [FIELD_PREFIX_ADDRESS + addr for addr in one_batch_addrs]
        batch_keys = {
            TABLE_STAKING_REWARDS: {
                "Keys": [{"field": k} for k in k_list]
            }
        }

        # Run batch read
        dynamodb = boto3.resource("dynamodb", "us-east-1")
        NUM_RETRIES = 5
        for i in range(NUM_RETRIES + 1):
            try:
                response = dynamodb.batch_get_item(RequestItems=batch_keys)
                break
            except ClientError as e:
                if i == NUM_RETRIES:
                    logging.info("Exhausted retries :(")
                    raise e

                sleep_seconds = random.randint(15, 45)
                logging.info("aws throughput exceeded.  Sleeping for %s seconds before retry...", sleep_seconds)
                time.sleep(sleep_seconds)

        # Process results into output
        out = {}
        for item in response["Responses"][TABLE_STAKING_REWARDS]:
            addr = item["field"][5:]
            addr_rewards = item["data"]
            out[addr] = addr_rewards

        # Make sure to have empty rewards result if address not in db.
        for addr in one_batch_addrs:
            if addr not in out:
                out[addr] = {}

        return out

    def _db_write_rewards(self, rewards_db):
        logging.info("_db_write_rewards() starting for %s addresses... ", len(rewards_db))
        addrs = list(rewards_db.keys())

        # Run batch write requests in parallel using pool of threads
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks to pool
            futures = []
            for i in range(0, len(addrs), TASK_SIZE_WRITE):
                task_addrs = addrs[i:i + TASK_SIZE_WRITE]
                future = executor.submit(self._batch_write, task_addrs, rewards_db)
                futures.append(future)
            logging.info("All tasks submitted. ")

            # Log progress of tasks completed
            num_write_items = 0
            for f in as_completed(futures):
                num_write_items += TASK_SIZE_WRITE
                if num_write_items % 10000 == 0:
                    logging.info("%s of %s writes completed ... ", num_write_items, len(addrs))
            logging.info("All tasks completed. ")

    def _batch_write(self, addrs, rewards_db):
        table = boto3.resource("dynamodb", "us-east-1").Table(TABLE_STAKING_REWARDS)

        with table.batch_writer() as batch:
            for addr in addrs:
                k = FIELD_PREFIX_ADDRESS + addr
                addr_rewards = rewards_db[addr]

                batch.put_item(Item={
                    "field": k,
                    "data": addr_rewards
                })

    def get_rewards_for_address(self, address, epochs_to_lookup):
        epochs = [str(epoch) for epoch in epochs_to_lookup]
        epoch_timestamps = self.get_epoch_timestamps()
        epochs_in_db = set(epoch_timestamps.keys())

        # Get rewards for address
        k = FIELD_PREFIX_ADDRESS + address
        addr_rewards = self._get(k)
        addr_rewards = {} if addr_rewards is None else addr_rewards

        # Fill in epochs with reward=0 if db has data for that epoch
        for epoch in epochs:
            if epoch in epochs_in_db and epoch not in addr_rewards:
                addr_rewards[epoch] = 0

        # Add timestamp field to output for each epoch/reward
        out = {}
        for epoch in epochs:
            if epoch in epochs_in_db:
                ts = epoch_timestamps[epoch]
                amount = addr_rewards[epoch]
                out[int(epoch)] = (ts, float(amount))

        return out


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
    answer = input("Type YES to proceed in writing all staking rewards for ALL users for ALL time "
                   "(that doesn't exist yet in db) to dynamodb.  "
                   "This might be an expensive operation.\n")
    if answer == "YES":
        rewards_all_users_write_db()
    else:
        print("Did not proceed.")
