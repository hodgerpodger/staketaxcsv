from staketaxcsv.common.progress import Progress
from staketaxcsv.luna2.config_luna2 import localconfig

SECONDS_PER_PAGE = 3


class ProgressLuna2(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
