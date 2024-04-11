import logging

from staketaxcsv.common.ibc.api_lcd_v1 import LcdAPI_v1


class CosmWasmLcdAPI(LcdAPI_v1):

    def contract_history(self, contract, sleep_seconds=0):
        uri_path = "/cosmwasm/wasm/v1/contract/{}/history".format(contract)
        logging.info("Querying lcd for contract history = %s ...", contract)
        data = self._query(uri_path, {}, sleep_seconds=sleep_seconds)
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


def contract_label(contract, localconfig, lcd_node):
    data = _get_contract_data(contract, localconfig, lcd_node)
    return data.get("contract_info", {}).get("label", "")


def _get_contract_data(contract, localconfig, lcd_node):
    if contract in localconfig.contracts:
        return localconfig.contracts[contract]

    data = CosmWasmLcdAPI(lcd_node).contract(contract)

    localconfig.contracts[contract] = data
    return data
