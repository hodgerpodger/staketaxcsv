import logging
import unittest
from staketaxcsv.sol.api_helius import HeliusAPI, get_token_symbols_no_limit
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

    @specialtest
    def test_get_token_symbols(self):
        mint_addresses = [
            "74DSHnK1qqr4z1pXjLjPAVi8XFngZ635jEVpdkJtnizQ",
            "31k88G5Mq7ptbRDf3AM13HAq6wRQHXHikR8hik7wPygk"
        ]
        symbols = HeliusAPI.get_token_symbols(mint_addresses)
        self.assertEqual(symbols[0], "COCO")
        self.assertEqual(symbols[1], "GP")

    @specialtest
    def test_get_token_symbols_no_limit(self):
        # Try with 1 address
        mint_addresses = ["74DSHnK1qqr4z1pXjLjPAVi8XFngZ635jEVpdkJtnizQ"]
        symbols = get_token_symbols_no_limit(mint_addresses)
        self.assertListEqual(symbols, ["COCO"])

        # Try with 101 addresses
        mint_addresses = ["74DSHnK1qqr4z1pXjLjPAVi8XFngZ635jEVpdkJtnizQ"] * 101
        symbols = get_token_symbols_no_limit(mint_addresses)
        self.assertListEqual(symbols, ["COCO"] * 101)

    @specialtest
    def test_get_token_symbols_no_limit_with_one_bad_address(self):
        mint_addresses = ["74DSHnK1qqr4z1pXjLjPAVi8XFngZ635jEVpdkJtnizQ"] * 101
        mint_addresses.append("somebadaddress")
        symbols = get_token_symbols_no_limit(mint_addresses)
        self.assertListEqual(symbols, ["COCO"] * 101 + [None])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
