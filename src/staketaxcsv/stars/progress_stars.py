from staketaxcsv.common.progress_rpc_nodes import ProgressRpc
from staketaxcsv.stars.config_stars import localconfig

SECONDS_PER_PAGE = 4
SECONDS_PER_TX = 0.7


class ProgressStars(ProgressRpc):

    def __init__(self):
        super().__init__(localconfig, SECONDS_PER_PAGE, SECONDS_PER_TX)
