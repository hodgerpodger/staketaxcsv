from staketaxcsv.btsg.config_btsg import localconfig
from staketaxcsv.common.progress import Progress

SECONDS_PER_PAGE = 4


class ProgressBTSG(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
