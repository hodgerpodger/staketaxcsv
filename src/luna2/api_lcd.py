import logging

from common.ibc.api_lcd import LcdAPI


class Luna2LcdAPI(LcdAPI):

    def contract_history(self, contract):
        uri_path = "/cosmwasm/wasm/v1/contract/{}/history".format(contract)
        logging.info("Querying lcd for contract = %s ...", contract)
        data = self._query(uri_path, {})
        return data

    def contract(self, contract):
        uri_path = "/cosmwasm/wasm/v1/contract/{}".format(contract)
        logging.info("Querying lcd for contract = %s ...", contract)
        data = self._query(uri_path, {}, sleep_seconds=0.1)
        return data
