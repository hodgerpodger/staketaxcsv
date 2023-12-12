import unittest
from staketaxcsv.sol.api_helius import HeliusAPI
from tests.settings_test import specialtest


class TestHeliusAPI(unittest.TestCase):

    @specialtest
    def test_get_token_symbol(self):
        symbol = HeliusAPI.get_token_symbol("31k88G5Mq7ptbRDf3AM13HAq6wRQHXHikR8hik7wPygk")
        self.assertEqual(symbol, "GP")

    @specialtest
    def test_get_token_symbol_bad_address(self):
        symbol = HeliusAPI.get_token_symbol("randomstring")
        self.assertEqual(symbol, None)
