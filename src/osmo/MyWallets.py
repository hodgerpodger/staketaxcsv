
from osmo.api_lcd import LcdAPI


class MyWallets:

    data = {}

    @classmethod
    def get(cls, wallet_address):
        """ Returns set of addresses that belong to this wallet address """
        if wallet_address in cls.data:
            return cls.data[wallet_address]

        cls.data[wallet_address] = set()

        # add wallet itself
        cls.data[wallet_address].add(wallet_address)

        # add reward wallet
        reward_wallet = LcdAPI.get_reward_address(wallet_address)
        if reward_wallet:
            cls.data[wallet_address].add(reward_wallet)

        return cls.data[wallet_address]
