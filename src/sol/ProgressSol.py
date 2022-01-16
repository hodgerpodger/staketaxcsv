import logging
import time

from sol.config_sol import localconfig

# Err on the side of overestimating for better user experience
SECONDS_PER_TOKEN_ADDRESS = 0.2
SECONDS_PER_STAKING_ADDRESS = 35
SECONDS_PER_TX = 0.95


class ProgressSol:
    def __init__(self):
        self.num_staking_addresses = 0
        self.txs_total = 0

    def set_estimate(self, num_staking_addresses, txs_total):
        self.num_staking_addresses = num_staking_addresses
        self.txs_total = txs_total

    def report_message(self, message):
        if localconfig.job:
            localconfig.job.set_message(message)
        else:
            logging.info(message)

    def report(self, stage, num, message):
        if stage == "txs":
            txs_left = self.txs_total - num
            staking_addrs_left = self.num_staking_addresses
        elif stage == "staking":
            txs_left = 0
            staking_addrs_left = self.num_staking_addresses - num
        else:
            raise ValueError(f"Bad condition: no stage={stage} found")

        seconds_left = SECONDS_PER_TX * txs_left + SECONDS_PER_STAKING_ADDRESS * staking_addrs_left

        # Write to db
        if localconfig.job:
            estimated_completion_timestamp = int(time.time() + seconds_left)
            localconfig.job.set_in_progress(message, estimated_completion_timestamp)
        else:
            logging.info("message: %s, seconds_left: %s", message, seconds_left)
