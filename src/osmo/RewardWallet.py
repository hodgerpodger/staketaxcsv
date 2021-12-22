
from osmo.api_lcd import LcdAPI


class RewardWallet:

    data = {}

    @classmethod
    def get(cls, wallet_address):
        """ Returns set of addresses that belong to this wallet address """
        if wallet_address in cls.data:
            return cls.data[wallet_address]

        cls.data[wallet_address] = LcdAPI.get_reward_address(wallet_address)
        return cls.data[wallet_address]
