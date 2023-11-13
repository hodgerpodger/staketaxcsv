from staketaxcsv.common.progress import Progress
from staketaxcsv.celestia.config_celestia import localconfig

SECONDS_PER_PAGE = 4
SECONDS_PER_TX = 0.7


class ProgressCelestia(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
