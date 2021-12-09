
import logging
import time
from atom.config_atom import localconfig

SECONDS_PER_PAGE = 15.0


class ProgressAtom():

    def __init__(self):
        self.pages = []

    def set_estimate(self, pages):
        self.pages = pages

    def report_message(self, message):
        if localconfig.job:
            localconfig.job.set_message(message)
        logging.info({"message": message})

    def report(self, page, message):
        pages_left = len(self.pages) - self.pages.index(page)

        # Estimate timestamp job finishes
        seconds_left = pages_left * SECONDS_PER_PAGE
        time_complete = int(time.time() + seconds_left)

        # Write to db
        if localconfig.job:
            localconfig.job.set_in_progress(message, time_complete)
