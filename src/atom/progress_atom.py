from atom.config_atom import localconfig
from common.progress import Progress

SECONDS_PER_PAGE = 15.0


class ProgressAtom(Progress):
    def __init__(self):
        super().__init__(localconfig)

    def set_estimate(self, sender_num_pages, receiver_num_pages):
        self.add_stage("sender", sender_num_pages, SECONDS_PER_PAGE)
        self.add_stage("receiver", receiver_num_pages, SECONDS_PER_PAGE)
