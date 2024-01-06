import os
import unittest

import staketaxcsv.settings_csv

DATADIR = os.path.dirname(os.path.realpath(__file__)) + "/data"


def specialtest(func):
    """ @specialtest

      * Decorator to only run if SPECIALTEST=1 is set in environment
      * Example usage: SPECIALTEST=1 python -m unittest
    """
    if not os.environ.get('SPECIALTEST'):
        return unittest.skip("Skipping special test")(func)
    return func


def rewards_db(func):
    """ @rewards_db_available

      * Decorator to only run if SOL_REWARDS_DB_READ is True
    """
    if not staketaxcsv.settings_csv.SOL_REWARDS_DB_READ:
        return unittest.skip("Skipping test when SOL_REWARDS_DB_READ=False")(func)
    return func


def mintscan_api(func):
    """ @mintscan_api

      * Decorator to only run if MINTSCAN_KEY is non-empty.
    """
    if not staketaxcsv.settings_csv.MINTSCAN_KEY:
        return unittest.skip("Skipping test requiring MINTSCAN_KEY")(func)
    return func
