import os
import unittest

DATADIR = os.path.dirname(os.path.realpath(__file__)) + "/data"


def specialtest(func):
    """ @specialtest : decorator that only runs if RUN_SPECIAL_TESTS=1 is set in environment """
    if not os.environ.get('RUN_SPECIAL_TESTS'):
        return unittest.skip("Skipping special test")(func)
    return func
