"""
IMPORTANT NOTE TO ADD TO ALL TEST FILES WITH ADDRESSES/TRANSACTIONS

DO NOT use personal addresses/transactions for tests.  Instead, choose relatively random
addresses/transactions.  For example, choose recent transactions from mintscan explorer for a
validator or contract.  This is to ensure good faith in maintaining privacy.

"""


import unittest
from tests.utils_sol import run_test


class TestSolRaydium(unittest.TestCase):

    def test_raydium_v4_swap(self):
        result = run_test(
            "Bdky9P44ETXheH3KTTURodpeaV7QdPJyofS4brK1656o",
            "5dk9JQExmdT635xMYA1RvdMTt7thpFoUXAi1MgtMzpEnADiq7TMMjpTG3wN8RHJ3ZqfuvtjsbDV5SHAWqRwiu51F"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount  sent_currency  fee  fee_currency  txid
2024-04-03 21:54:39  TRADE    0.05388719       weWETH             0.971735668  SOL                               5dk9JQExmdT635xMYA1RvdMTt7thpFoUXAi1MgtMzpEnADiq7TMMjpTG3wN8RHJ3ZqfuvtjsbDV5SHAWqRwiu51F
-------------------  -------  ---------------  -----------------  -----------  -------------  ---  ------------  ----------------------------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)

    def test_raydium_v4_swap_case_2(self):
        result = run_test(
            "mm5G1iYsa87dCR7zwBHmDC57k7mA6HHiRTE8FFNpkju",
            "2rY9ky2Ypps3KMxcgEoerPPKc1ZYEhxbV7x2bRZf8n31RuBDddvguvdmWMLyDJB8ayvbcUGH2LPpxDhT2rhubTEX"
        )
        correct_result = """
-------------------  -------  ---------------  -----------------  --------------  --------------------------------------------  ---  ------------  ----------------------------------------------------------------------------------------
timestamp            tx_type  received_amount  received_currency  sent_amount     sent_currency                                 fee  fee_currency  txid
2024-04-03 21:54:39  TRADE    0.045110273      SOL                7287032.271779  JB5TxxRchPN1kBt6oWNURAC5DAnz88SeX2BeQEamMQva                     2rY9ky2Ypps3KMxcgEoerPPKc1ZYEhxbV7x2bRZf8n31RuBDddvguvdmWMLyDJB8ayvbcUGH2LPpxDhT2rhubTEX
-------------------  -------  ---------------  -----------------  --------------  --------------------------------------------  ---  ------------  ----------------------------------------------------------------------------------------
        """
        self.assertEqual(result, correct_result.strip(), result)
