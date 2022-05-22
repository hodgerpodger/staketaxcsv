from common.progress import Progress
from dvpn.config_dvpn import localconfig

SECONDS_PER_PAGE = 2


class ProgressDvpn(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_lcd_estimate(self, count_pages):
        self.add_stage("lcd", count_pages, SECONDS_PER_PAGE)

    def set_rpc_estimate(self, count_pages):
        self.add_stage("rpc", count_pages, SECONDS_PER_PAGE)
