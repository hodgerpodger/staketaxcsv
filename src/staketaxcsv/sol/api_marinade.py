# https://native-staking.marinade.finance/docs

import logging
import requests


class MarinadeAPI:
    session = requests.Session()

    @classmethod
    def native_staking_rewards(cls, user_address):
        logging.info("Querying marinade native staking rewards ...")
        url = "https://native-staking.marinade.finance/v1/user-rewards"
        params = {"user": user_address}

        response = cls.session.get(url, params=params)
        data = response.json()

        return data
