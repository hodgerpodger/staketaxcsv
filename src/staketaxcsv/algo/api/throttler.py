import logging
from datetime import datetime
from threading import Lock
from time import sleep

logger = logging.getLogger()


class LeakyBucketThrottler(object):
    _current_bucket = None
    _capacity = 0
    _max_capacity = 0
    _lock = None


    def __init__(self, max_capacity):
        self._current_bucket = datetime.now()
        self._capacity = 0
        self._max_capacity = max_capacity
        self._lock = Lock()

    def _requires_new_bucket(self, current_time):
        if self._current_bucket.minute < current_time.minute:
            return True
        elif self._current_bucket.minute == current_time.minute:
            if self._current_bucket.second < current_time.second:
                return True
            elif self._current_bucket.second > current_time.second:
                assert False, "Should never reach here."
        else:
            assert False, "Should never ever reach here."

        return False

    def _create_new_bucket(self):
        self._capacity = 0
        self._current_bucket = datetime.now()

    def fill_request(self):
        with self._lock:
            current_time = datetime.now()
            if self._requires_new_bucket(current_time):
                self._create_new_bucket()

            if self._capacity > self._max_capacity:
                time_to_wait = (current_time.microsecond - self._current_bucket.microsecond) / (1000 * 1000)

                logger.debug("Algorand throttler waiting for %f seconds.", time_to_wait)

                sleep(time_to_wait)
                self._create_new_bucket()

            self._capacity += 1
