from staketaxcsv.common.progress import Progress
from staketaxcsv.dvpn.config_dvpn import localconfig

LCD_SECONDS_PER_PAGE = 3
RPC_SECONDS_PER_PAGE = 2
USAGE_PAYMENTS_SECONDS_PER_PAGE = 2


class ProgressDvpn(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_lcd_estimate(self, count_pages):
        self.add_stage("lcd", count_pages, LCD_SECONDS_PER_PAGE)

    def set_rpc_estimate(self, count_pages):
        self.add_stage("rpc", count_pages, RPC_SECONDS_PER_PAGE)

    def set_usage_payment_estimate(self, count_pages):
        self.add_stage("usage-payment", count_pages, USAGE_PAYMENTS_SECONDS_PER_PAGE)
