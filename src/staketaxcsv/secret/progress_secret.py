from staketaxcsv.common.progress import Progress
from staketaxcsv.secret.config_secret import localconfig

SECONDS_PER_PAGE = 4


class ProgressSecret(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
