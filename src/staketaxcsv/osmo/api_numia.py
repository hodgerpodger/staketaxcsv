import logging
import time
from urllib.parse import quote
import requests
from staketaxcsv.settings_csv import NUMIA_API_DOMAIN, NUMIA_API_TOKEN


class NumiaAPI:
    """Numia API for fetching reward data."""
    session = requests.Session()

    def __init__(self):
        if not NUMIA_API_TOKEN:
            raise Exception("Missing NUMIA_API_TOKEN environment variable.")

        self.base_url = f"https://{NUMIA_API_DOMAIN}"
        self.headers = {
            'Authorization': f'Bearer {NUMIA_API_TOKEN}',
            'Accept': 'application/json'
        }

    def _query(self, uri_path, query_params, sleep_seconds=0.1):
        url = self.base_url + uri_path
        encoded_query = "&".join(f"{quote(str(k))}={quote(str(v))}" for k, v in query_params.items())
        logging.info("Requesting URL: %s?%s ...", url, encoded_query)

        response = self.session.get(url, headers=self.headers, params=query_params)
        if response.status_code == 401:
            raise Exception("Unauthorized: Check NUMIA_API_TOKEN.")
        if response.status_code == 429:
            raise Exception("Rate limit exceeded: Consider reducing query frequency.")

        response.raise_for_status()
        data = response.json()

        if sleep_seconds:
            time.sleep(sleep_seconds)
        return data

    def get_reward_denoms(self, wallet_address):
        """Fetch all reward denominations for a given wallet address."""
        uri_path = f"/rewards/token/{quote(wallet_address)}"
        data = self._query(uri_path, {})
        return data.get("denoms", [])

    def get_rewards(self, wallet_address, denom):
        """Fetch rewards for a specific wallet address and denomination."""
        encoded_denom = quote(denom, safe='')
        uri_path = f"/rewards/token/{quote(wallet_address)}/{encoded_denom}"
        data = self._query(uri_path, {})
        return data
