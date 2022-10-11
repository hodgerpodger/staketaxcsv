from staketaxcsv.common.progress import Progress
from staketaxcsv.huahua.config_huahua import localconfig

SECONDS_PER_PAGE = 4


class ProgressHuahua(Progress):

    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, count_pages):
        self.add_stage("default", count_pages, SECONDS_PER_PAGE)
