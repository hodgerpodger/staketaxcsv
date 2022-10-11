from staketaxcsv.common.progress import Progress
from staketaxcsv.luna1.config_luna1 import localconfig

# Err on the side of overestimating for better user experience
SECONDS_PER_TX_FETCH = 0.2
SECONDS_PER_TX_PROCESS = 0.2


class ProgressTerra(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, num_txs):
        self.add_stage("default", num_txs, SECONDS_PER_TX_FETCH)
        self.add_stage("process_txs", num_txs, SECONDS_PER_TX_PROCESS)
