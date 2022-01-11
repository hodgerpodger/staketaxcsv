import logging
import time

from terra.config_terra import localconfig

# Err on the side of overestimating for better user experience
SECONDS_PER_TX = 0.1


class ProgressTerra():

    def __init__(self):
        self.num_txs = 0

    def set_estimate(self, num_txs):
        self.num_txs = num_txs

    def report_message(self, message):
        if localconfig.job:
            localconfig.job.set_message(message)
        logging.info({"message": message})

    def report(self, num, message):
        txs_left = self.num_txs - num

        seconds_left = txs_left * SECONDS_PER_TX
        time_complete = int(time.time() + seconds_left)

        # Write to db
        if localconfig.job:
            localconfig.job.set_in_progress(message, time_complete)
        else:
            logging.info("message: %s, seconds_left: %s", message, seconds_left)
