from atom.config_atom import localconfig
from common.progress import Progress

SECONDS_PER_PAGE = 5


class ProgressAtom(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
