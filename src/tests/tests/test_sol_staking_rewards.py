import json
import logging
import pprint
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
@patch("staketaxcsv.sol.staking_rewards.RpcAPI", new=MockRpcAPI)
class TestSolStakingRewards(unittest.TestCase):
    rewards_gold = None

    @classmethod
    def setUpClass(cls):
        with open(REWARDS_GOLD_JSON, "r") as f:
            data = json.load(f)

        # Convert the list of lists to a list of tuples
        cls.rewards_gold = [tuple(item) for item in data]

    @patch("staketaxcsv.sol.staking_rewards.SOL_REWARDS_DB_READ", False)
    @patch("staketaxcsv.sol.staking_rewards.RpcAPI.get_latest_epoch", return_value=142)
    @patch("staketaxcsv.sol.staking_rewards_common.RpcAPI", MockRpcAPI)
    def test_rewards_using_rpc(self, mock_get_lastest_epoch):
        logging.basicConfig(level=logging.INFO)
        result = staking_rewards._rewards(STAKING_ADDRESS)
        self.assertEqual(result[:10], self.rewards_gold[:10])

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
    # create_gold_json_file()
    logging.basicConfig(level=logging.INFO)
    unittest.main()
