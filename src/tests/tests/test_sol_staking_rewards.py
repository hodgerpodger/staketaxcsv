"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import json
import logging
import unittest
from unittest.mock import patch

from tests.settings_test import specialtest, rewards_db, DATADIR
from tests.mock_sol import MockRpcAPI
from staketaxcsv.settings_csv import SOL_REWARDS_DB_READ, TICKER_SOL
from staketaxcsv.sol import staking_rewards
STAKING_ADDRESS = "F6dEJnUbV999jwHdA6GPb1YhwfcyPfDXq9LcwMkUFbLr"

# has rewards for F6dEJN.. for epochs 132-545
REWARDS_GOLD_JSON = DATADIR + "/" + TICKER_SOL + "/rewards." + STAKING_ADDRESS + ".json"


@specialtest
class TestSolStakingRewards(unittest.TestCase):
    rewards_gold = None

    @classmethod
    def setUpClass(cls):
        with open(REWARDS_GOLD_JSON, "r") as f:
            data = json.load(f)

        # Convert the list of lists to a list of tuples
        cls.rewards_gold = [tuple(item) for item in data]

    @patch("staketaxcsv.sol.staking_rewards.SOL_REWARDS_DB_READ", False)
    @patch("staketaxcsv.sol.staking_rewards.RpcAPI", new=MockRpcAPI)
    @patch("staketaxcsv.sol.staking_rewards_common.RpcAPI", new=MockRpcAPI)
    @patch("staketaxcsv.sol.staking_rewards.get_epochs_all", return_value=list(range(132, 137)))
    def test_rewards_using_rpc(self, mock_get_epochs_all):
        result = staking_rewards._rewards(STAKING_ADDRESS)
        self.assertEqual(result[:5], self.rewards_gold[:5])

    def test_lookup_reward_via_rpc(self):
        # test pre-epoch 651

        staking_address = "2gkKivvDqc4gn2JXNfPjhSgyeE4U4SGxjrvpo6E5gkeK"
        ts, amount = staking_rewards._lookup_reward_via_rpc(staking_address, 645)
        self.assertEqual(ts, "2024-07-22 19:54:28")
        self.assertEqual(amount, 32.404371735)

        # test epoch 651+ to make sure difference in getInflationReward return slot result difference
        # doesn't cause issues

        staking_address = "2gkKivvDqc4gn2JXNfPjhSgyeE4U4SGxjrvpo6E5gkeK"
        ts, amount = staking_rewards._lookup_reward_via_rpc(staking_address, 655)
        self.assertEqual(ts, "2024-08-13 17:49:42")
        self.assertEqual(amount, 32.538007227)
        staking_address = "61H9wkgj4KYWDXA7zJSRWy974iDhnsCVjvUQTNAKHmfR"
        ts, amount = staking_rewards._lookup_reward_via_rpc(staking_address, 654)
        self.assertEqual(ts, "2024-08-11 15:17:17")
        self.assertEqual(amount, 16.961246909)

    @rewards_db
    def test_rewards_using_db(self):
        result = staking_rewards._rewards(STAKING_ADDRESS)
        self.assertEqual(result[:400], self.rewards_gold[:400])

        # Make sure all epochs are in rewards result
        self.assertEqual([x[0] for x in result[:400]], list(range(132, 532)))

    @rewards_db
    def test_rewards_using_db_start_date_only(self):
        result = staking_rewards._rewards(STAKING_ADDRESS, start_date="2023-12-12")
        self.assertEqual(result[:2], [
            (544, "2023-12-12 08:28:18", 12.038016226),
            (545, "2023-12-14 15:53:54", 12.131610051),
        ])

        result = staking_rewards._rewards(STAKING_ADDRESS, start_date="2023-12-13")
        self.assertEqual(result[:1], [
            (545, "2023-12-14 15:53:54", 12.131610051)
        ])

        result = staking_rewards._rewards(STAKING_ADDRESS, start_date="2001-01-01")
        self.assertEqual(result[:400], self.rewards_gold[:400])

        result = staking_rewards._rewards(STAKING_ADDRESS, start_date="2099-01-01")
        self.assertEqual(result, [])

    @rewards_db
    def test_rewards_using_db_end_date_only(self):
        result = staking_rewards._rewards(STAKING_ADDRESS, end_date="2020-12-28")
        self.assertEqual(result[:2], [
            (132, "2020-12-26 10:58:10", 0.056222434),
            (133, "2020-12-28 21:05:16", 0.055973666),
        ])

        result = staking_rewards._rewards(STAKING_ADDRESS, end_date="2020-12-27")
        self.assertEqual(result[:1], [
            (132, "2020-12-26 10:58:10", 0.056222434),
        ])

        result = staking_rewards._rewards(STAKING_ADDRESS, end_date="2099-01-01")
        self.assertEqual(result[:400], self.rewards_gold[:400])

        result = staking_rewards._rewards(STAKING_ADDRESS, end_date="2001-01-01")
        self.assertEqual(result, [])

    @rewards_db
    def test_rewards_using_db_with_start_date_end_date(self):
        result = staking_rewards._rewards(STAKING_ADDRESS, start_date="2023-12-07", end_date="2023-12-10")
        self.assertEqual(result, [
            (542, "2023-12-07 18:40:24", 12.097090153),
            (543, "2023-12-10 01:17:22", 12.124528007)
        ])

        result = staking_rewards._rewards(STAKING_ADDRESS, start_date="2023-12-08", end_date="2023-12-10")
        self.assertEqual(result, [
            (543, "2023-12-10 01:17:22", 12.124528007)
        ])

        result = staking_rewards._rewards(STAKING_ADDRESS, start_date="2001-01-01", end_date="2099-01-01")
        self.assertEqual(result[:400], self.rewards_gold[:400])


def create_gold_json_file():
    data = staking_rewards._rewards(STAKING_ADDRESS)
    with open(REWARDS_GOLD_JSON, "w") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # create_gold_json_file()
    unittest.main()
