import logging
import time

from osmo.config_osmo import localconfig

SECONDS_PER_TX = 0.6
SECONDS_PER_REWARD_TOKEN = 2.0


class ProgressOsmo:
    def __init__(self):
        self.num_txs = 0
        self.num_reward_tokens = 0
        self.time_start = time.time()

    def set_estimate(self, num_txs, num_reward_tokens):
        self.num_txs = num_txs
        self.num_reward_tokens = num_reward_tokens

    def report_message(self, message):
        if localconfig.job:
            localconfig.job.set_message(message)
        logging.info({"message": message})

    def report(self, stage, num, message):
        if stage == "_fetch_and_process_txs":
            txs_left = self.num_txs - num
            reward_tokens_left = self.num_reward_tokens
        elif stage == "lp_rewards":
            txs_left = 0
            reward_tokens_left = self.num_reward_tokens - num
        else:
            raise ValueError(f"Bad stage={stage} in ProgressOsmo.report()")

        seconds_left = SECONDS_PER_TX * txs_left + SECONDS_PER_REWARD_TOKEN * reward_tokens_left

        # Write to db
        if localconfig.job:
            estimated_completion_timestamp = int(time.time() + seconds_left)
            localconfig.job.set_in_progress(message, estimated_completion_timestamp)
        else:
            logging.info(
                "message: %s, seconds_left: %s, time_elapsed: %s", message, seconds_left, time.time() - self.time_start
            )
