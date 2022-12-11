from staketaxcsv.common.progress import Progress
from staketaxcsv.sifchain.config_sifchain import localconfig

SECONDS_PER_PAGE = 4


class ProgressSifchain(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
