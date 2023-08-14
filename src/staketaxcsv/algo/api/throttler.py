import logging
import time
from datetime import datetime
from threading import Lock
from time import sleep

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class LeakyBucketThrottler(object):
    _current_bucket = None
    _capacity = 0
    _max_capacity = 0
    _lock = None


    def __init__(self, max_capacity):
        self._current_bucket = time.time()
        self._capacity = 0
        self._max_capacity = max_capacity
        self._lock = Lock()

    def _requires_new_bucket(self, current_time):
        diff = current_time - self._current_bucket
        return diff >= 1

    def _create_new_bucket(self):
        self._capacity = 0
        self._current_bucket = time.time()

    def fill_request(self):
        with self._lock:
            current_time = time.time()
            if self._requires_new_bucket(current_time):
                self._create_new_bucket()
                logger.debug('Reset capacity')

            if self._capacity > self._max_capacity:
                time_to_wait = current_time - self._current_bucket

                print(current_time, self._current_bucket)
                logger.debug("Algorand throttler waiting for %f seconds.", time_to_wait)

                sleep(time_to_wait)
                self._create_new_bucket()

            self._capacity += 1
