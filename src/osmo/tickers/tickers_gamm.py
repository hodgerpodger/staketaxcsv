
"""
usage: python3 osmo/tickers/tickers_gamm.py
  * Refreshes osmo/tickers/tickers_gamm.json

Source info can be found at https://osmosis.stakesystems.io/cosmos/bank/v1beta1/denoms_metadata
  * has display name and exponent info per pool
  * everything was identical.  So I just hardcoded.
"""


class TickersGAMM:

    @classmethod
    def lookup(cls, gamm_address):
        # i.e. gamm/pool/6
        _, _, num = gamm_address.split("/")
        return "GAMM-{}".format(num)
