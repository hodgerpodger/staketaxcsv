import logging

import requests
from staketaxcsv.settings_csv import ALGO_NFDOMAINS


# API documentation: https://editor.swagger.io/?url=https://api.testnet.nf.domains/info/openapi3.yaml
class NFDomainsAPI:
    session = requests.Session()

    def get_address(self, name):
        endpoint = f"nfd/{name}"
        params = {"view": "brief"}

        data, status_code = self._query(ALGO_NFDOMAINS, endpoint, params)

        if status_code == 200:
            # https://docs.nf.domains/docs/faq#how-do-i-set-my-address-to-resolve-my-nfd
            # If present, use the primary/deposit address, otherwise resolve to the owner address
            if "caAlgo" in data:
                return data["caAlgo"][0]
            else:
                return data["owner"]
        else:
            return None

    def _query(self, base_url, endpoint, params=None):
        logging.info("Querying NFDomains endpoint %s...", endpoint)
        url = f"{base_url}/{endpoint}"
        response = self.session.get(url, params=params)
        return response.json(), response.status_code
