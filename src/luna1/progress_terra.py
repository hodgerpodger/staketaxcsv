from common.progress import Progress
from luna1.config_luna1 import localconfig

# Err on the side of overestimating for better user experience
SECONDS_PER_TX = 0.1


class ProgressTerra(Progress):
    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, num_txs):
        self.add_stage('default', num_txs, SECONDS_PER_TX)
