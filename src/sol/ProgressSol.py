
import logging
import time
from sol.config_sol import localconfig

# Err on the side of overestimating for better user experience
SECONDS_PER_TOKEN_ADDRESS = 0.2
SECONDS_PER_STAKING_ADDRESS = 35
SECONDS_PER_TX = .95


class ProgressSol():

    def __init__(self):
        self.num_staking_addresses = 0
        self.txs_total = 0
        self.time_start = None

    def set_estimate(self, num_staking_addresses, txs_total):
        self.num_staking_addresses = num_staking_addresses
        self.txs_total = txs_total
        self.time_start = time.time()

    def report_message(self, message):
        if localconfig.job:
            localconfig.job.set_message(message)
        else:
            logging.info(message)

    def report(self, stage, num, message):
        if stage == "txs":
            staking_addrs_left = self.num_staking_addresses
            txs_left = self.txs_total - num
        elif stage == "staking":
            staking_addrs_left = self.num_staking_addresses - num
            txs_left = 0
        else:
            raise Exception("Bad condition: no stage={} found".format(stage))

        seconds_left = sum([
            staking_addrs_left * SECONDS_PER_STAKING_ADDRESS,
            txs_left * SECONDS_PER_TX
        ])

        # Estimate timestamp job finishes
        time_complete = int(time.time() + seconds_left)

        # Write to db
        if localconfig.job:
            localconfig.job.set_in_progress(message, time_complete)
        else:
            logging.info("message: %s, seconds_left: %s", message, seconds_left)
