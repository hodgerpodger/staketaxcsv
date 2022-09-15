import logging

from staketaxcsv.common.ibc.api_lcd import LcdAPI


class CosmWasmLcdAPI(LcdAPI):

    def contract_history(self, contract):
        uri_path = "/cosmwasm/wasm/v1/contract/{}/history".format(contract)
        logging.info("Querying lcd for contract history = %s ...", contract)
        data = self._query(uri_path, {})
        return data

    def contract(self, contract):
        uri_path = "/cosmwasm/wasm/v1/contract/{}".format(contract)
        logging.info("Querying lcd for contract = %s ...", contract)
        data = self._query(uri_path, {}, sleep_seconds=0.1)
        return data


def extract_msg(data):
    for entry in data["entries"]:
        if entry["operation"] == "CONTRACT_CODE_HISTORY_OPERATION_TYPE_INIT":
            msg = entry["msg"]
            return msg

    return None
