from common.progress import Progress
from sol.config_sol import localconfig

# Err on the side of overestimating for better user experience
SECONDS_PER_TOKEN_ADDRESS = 0.2
SECONDS_PER_STAKING_ADDRESS = 35
SECONDS_PER_TX = 0.95


class ProgressSol(Progress):
    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, num_staking_addresses, txs_total):
        self.add_stage("txs", txs_total, SECONDS_PER_TX)
        self.add_stage("staking", num_staking_addresses, SECONDS_PER_STAKING_ADDRESS)

    def update_estimate(self, num_staking_addresses):
        self.stages["staking"].total_tasks = num_staking_addresses
