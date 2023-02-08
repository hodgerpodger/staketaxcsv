from staketaxcsv.common.progress_rpc_nodes import ProgressRpc
from staketaxcsv.juno.config_juno import localconfig

SECONDS_PER_PAGE = 4
SECONDS_PER_TX = 0.7


class ProgressJuno(ProgressRpc):

    def __init__(self):
        super().__init__(localconfig, SECONDS_PER_PAGE, SECONDS_PER_TX)
