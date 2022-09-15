from staketaxcsv.common.progress import Progress
from staketaxcsv.stars.config_stars import localconfig

SECONDS_PER_PAGE = 4


class ProgressStars(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
