

import logging
import time
from osmo.config_osmo import localconfig

SECONDS_PER_TX = 0.1


class ProgressOsmo():

    def __init__(self):
        self.num_txs = 0

    def set_estimate(self, num_txs):
        self.num_txs = num_txs

    def report_message(self, message):
        if localconfig.job:
            localconfig.job.set_message(message)
        logging.info({"message": message})

    def report(self, num_tx):
        txs_left = self.num_txs - num_tx

        # Estimate timestamp job finishes
        seconds_left = txs_left * SECONDS_PER_TX
        time_complete = int(time.time() + seconds_left)

        # Write to db
        if localconfig.job:
            message = "Retrieving transaction {} of {}".format(num_tx + 1, self.num_txs)
            localconfig.job.set_in_progress(message, time_complete)
