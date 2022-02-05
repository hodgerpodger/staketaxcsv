from common.progress import Progress
from iotex.config_iotex import localconfig

# Err on the side of overestimating for better user experience
SECONDS_PER_TX = 0.01


class ProgressIotex(Progress):
    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, num_txs):
        self.add_stage("default", num_txs, SECONDS_PER_TX)
