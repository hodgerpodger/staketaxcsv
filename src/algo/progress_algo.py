from algo.config_algo import localconfig
from common.progress import Progress

# Err on the side of overestimating for better user experience
SECONDS_PER_TX = 0.1


class ProgressAlgo(Progress):
    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, num_txs):
        self.add_stage("default", num_txs, SECONDS_PER_TX)
