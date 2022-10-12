from staketaxcsv.common.progress import Progress
from staketaxcsv.kuji.config_kuji import localconfig

SECONDS_PER_PAGE = 4


class ProgressKuji(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
