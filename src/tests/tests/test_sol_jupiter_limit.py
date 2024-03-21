"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""

import unittest
from tests.utils_sol import run_test_txids


class TestSolJupiter(unittest.TestCase):

    def test_jupiter_limit_order_series(self):
        result = run_test_txids(
            "GAgnD5XviS4wN7GpcTBbgvtFAZnT6Lc1ehkbnP3qo1bz",
            [
                "5iPvQ1ThjpbMCYSqTwCYvMBfMrr4ysiEZeAF9goRgqtfAqePymck3sGFZQ4RnseWBVvfrH45WgZKndSB5XEvy7sk",
                "4xqxLBqu1ju8eRKb2YiazZxDCdJbLQ8Eh4nEE1zE2WN7GLoyfCes4Cs4fHAcvpf6yNocNv77DfN6oEC7CyYrKAza",
                "42zg3fooJY4TNf1DBJF4iaFXdE4ZmssX27JpMCSVPmUPA9et2neKND3H8NYViRx4yv2xDjcyZLnBewN3bC2mApXN",
                "3HxfYpPAC7dMAoWSDA8ZmZ1V2173ydk51stHrH45VGg9Ykgrr9p676aJwQE2eRJQJ36Bw3hZY5pbpDWhBimGaHNi",
                "DHFysLFq77hbVeDhUF7iJXvyDhBX2M26Ji6MoYTcdFLpq83BewvmevvXtKWYBg34Ze3S719ywzo1qWS2fzaot5M",
                "4vug6xbfY6xpk81oA6p2gJzoA8eb9nowdB3mnNiF97QWiW5cPRXWh3cRutKrGCFbonML7JjLo5xJzuXAntRzN3MZ",
                "QFgRtoQK5B4ZMjozD6GmqLkqjaFqhQ7ynJYxGjr9wzNqCTXhNS9NHETuEpsXVmSJokSfPYxAFHdLrivY8CNrYek",
                "3HdFhHNyf2uKrW6zb6FeYZpjcRyvprQuQH4oVkmc4uuCAhoEUAEkPHgUzRubf8npmHnziRs4HokFTgAkGPyzso6D",
                "5FBWfqrMYoYbqq6yBWJUtqbVmCDAcz79M7NrzB1yxNLibzMWjndHsVRvwDMkUNgwr58KdLP7pCBjkwhnHrbTre5k",
                "4NAC7cK6cRPFZJaJVehTJ2Pstj63oWjcDnnFoPARtsXb4qZiHhQeQmG9wbZg2yTkNPm37h13hP9vdZQdJReHiLBF",
                "4v28RP4AadGTfSRmYyZyag2erNokm6pyE7Fdct14bkEKSDFusPkxkp2DLSovxuGPnRA6qJdmFFQrJHCouq6RaNrw",
            ]
        )
        correct_result = """
-------------------  -------------------  ---------------  --------------------------------------------  -----------  -------------  ---------  ------------  ----------------------------------------------------------------------------------------
timestamp            tx_type              received_amount  received_currency                             sent_amount  sent_currency  fee        fee_currency  txid
2024-03-18 21:34:47  _JUPITER_LIMIT_OPEN                                                                                                                      5iPvQ1ThjpbMCYSqTwCYvMBfMrr4ysiEZeAF9goRgqtfAqePymck3sGFZQ4RnseWBVvfrH45WgZKndSB5XEvy7sk
2024-03-18 21:58:18  TRADE                0.000177317      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  399.36       USDC                                    4xqxLBqu1ju8eRKb2YiazZxDCdJbLQ8Eh4nEE1zE2WN7GLoyfCes4Cs4fHAcvpf6yNocNv77DfN6oEC7CyYrKAza
2024-03-18 21:58:46  TRADE                0.000007105      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  16.0         USDC                                    42zg3fooJY4TNf1DBJF4iaFXdE4ZmssX27JpMCSVPmUPA9et2neKND3H8NYViRx4yv2xDjcyZLnBewN3bC2mApXN
2024-03-18 21:59:08  TRADE                0.000888001      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  2000.0       USDC                                    3HxfYpPAC7dMAoWSDA8ZmZ1V2173ydk51stHrH45VGg9Ykgrr9p676aJwQE2eRJQJ36Bw3hZY5pbpDWhBimGaHNi
2024-03-18 21:59:26  TRADE                0.000177601      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  400.0        USDC                                    DHFysLFq77hbVeDhUF7iJXvyDhBX2M26Ji6MoYTcdFLpq83BewvmevvXtKWYBg34Ze3S719ywzo1qWS2fzaot5M
2024-03-18 21:59:30  TRADE                0.000682030      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  1536.1024    USDC                                    4vug6xbfY6xpk81oA6p2gJzoA8eb9nowdB3mnNiF97QWiW5cPRXWh3cRutKrGCFbonML7JjLo5xJzuXAntRzN3MZ
2024-03-18 23:27:17  TRADE                0.000481527      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  1084.519219  USDC                                    QFgRtoQK5B4ZMjozD6GmqLkqjaFqhQ7ynJYxGjr9wzNqCTXhNS9NHETuEpsXVmSJokSfPYxAFHdLrivY8CNrYek
2024-03-19 01:06:03  TRADE                0.000081057      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  182.560735   USDC                                    3HdFhHNyf2uKrW6zb6FeYZpjcRyvprQuQH4oVkmc4uuCAhoEUAEkPHgUzRubf8npmHnziRs4HokFTgAkGPyzso6D
2024-03-19 01:06:16  TRADE                0.000081057      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  182.560735   USDC                                    5FBWfqrMYoYbqq6yBWJUtqbVmCDAcz79M7NrzB1yxNLibzMWjndHsVRvwDMkUNgwr58KdLP7pCBjkwhnHrbTre5k
2024-03-19 01:08:47  TRADE                0.000372862      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  839.779382   USDC                                    4NAC7cK6cRPFZJaJVehTJ2Pstj63oWjcDnnFoPARtsXb4qZiHhQeQmG9wbZg2yTkNPm37h13hP9vdZQdJReHiLBF
2024-03-19 01:10:56  TRADE                0.001491447      9gr84rGyLvVasmqXvj65njjUgKyBemKWSJsvijTPmcQz  3359.117529  USDC           0.0020772  SOL           4v28RP4AadGTfSRmYyZyag2erNokm6pyE7Fdct14bkEKSDFusPkxkp2DLSovxuGPnRA6qJdmFFQrJHCouq6RaNrw
-------------------  -------------------  ---------------  --------------------------------------------  -----------  -------------  ---------  ------------  ----------------------------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
