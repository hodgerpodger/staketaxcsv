from staketaxcsv.common.progress import Progress

SECONDS_PER_PAGE = 2


class ProgressMintScan(Progress):

    def __init__(self, localconfig):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
