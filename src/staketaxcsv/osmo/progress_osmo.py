from staketaxcsv.common.progress import Progress
from staketaxcsv.osmo.config_osmo import localconfig

SECONDS_PER_PAGE = 15
SECONDS_PER_REWARD_TOKEN = 2.0


class ProgressOsmo(Progress):
    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, num_pages, num_reward_tokens):
        self.add_stage("txs", num_pages, SECONDS_PER_PAGE)
        self.add_stage("lp_rewards", num_reward_tokens, SECONDS_PER_REWARD_TOKEN)
