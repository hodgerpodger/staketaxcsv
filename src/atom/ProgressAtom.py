import logging
import time

from atom.config_atom import localconfig

SECONDS_PER_PAGE = 15.0


class ProgressAtom:
    def __init__(self):
        self.num_pages = 0

    def set_estimate(self, num_pages):
        self.num_pages = num_pages

    def report_message(self, message):
        if localconfig.job:
            localconfig.job.set_message(message)
        logging.info({"message": message})

    def report(self, page, message):
        pages_left = self.num_pages - page
        seconds_left = pages_left * SECONDS_PER_PAGE

        # Write to db
        if localconfig.job:
            estimated_completion_timestamp = int(time.time() + seconds_left)
            localconfig.job.set_in_progress(message, estimated_completion_timestamp)
        logging.info("message: %s, seconds_left: %s", message, seconds_left)
