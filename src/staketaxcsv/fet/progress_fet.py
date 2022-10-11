from staketaxcsv.common.progress import Progress
from staketaxcsv.fet.config_fet import localconfig

SECONDS_PER_PAGE = 3
SECONDS_PER_TX_RPC = 0.55


class ProgressFet(Progress):
    STAGE_FET1_PAGES = "fet1_pages"
    STAGE_FET1_TXS = "fet1_txs"
    STAGE_FET2 = "fet2"
    STAGE_FET3 = "fet3"
    STAGE_FET4 = "fet4"

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate_fet1(self, count_pages, count_txs):
        self.add_stage(self.STAGE_FET1_PAGES, count_pages, SECONDS_PER_PAGE)
        self.add_stage(self.STAGE_FET1_TXS, count_txs, SECONDS_PER_TX_RPC)

    def set_estimate_fet2(self, count_pages):
        self.add_stage(self.STAGE_FET2, count_pages, SECONDS_PER_PAGE)

    def set_estimate_fet3(self, count_pages):
        self.add_stage(self.STAGE_FET3, count_pages, SECONDS_PER_PAGE)

    def set_estimate_fet4(self, count_pages):
        self.add_stage(self.STAGE_FET4, count_pages, SECONDS_PER_PAGE)
