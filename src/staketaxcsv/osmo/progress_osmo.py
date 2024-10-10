from staketaxcsv.common.progress import Progress
from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.common.ibc.progress_mintscan import ProgressMintScan, SECONDS_PER_PAGE


SECONDS_PER_REWARD_TOKEN = 2.0
SECONDS_PER_TRANSACTION = 0.13


class ProgressOsmo(ProgressMintScan):

    def __init__(self, localconfig):
        super().__init__(localconfig)

    def set_estimate_process_transactions_stage(self, num_transactions):
        self.add_stage("process_transactions", num_transactions, SECONDS_PER_TRANSACTION)

    def set_estimate_lp_rewards_stage(self, num_reward_tokens):
        self.add_stage("lp_rewards", num_reward_tokens, SECONDS_PER_REWARD_TOKEN)
