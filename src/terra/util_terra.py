""" Parsing and utility functions for fcd tx info """

import base64
import json
import logging

from terra.api_lcd import LcdAPI
from terra.config_terra import localconfig
from terra.constants import CUR_ORION, IBC_TOKEN_NAMES, MILLION


def _contracts(elem):
    out = []

    count = len(elem["tx"]["value"]["msg"])
    for i in range(count):
        out.append(_contract(elem, i))
    return out


def _contract(elem, index=0):
    return elem["tx"]["value"]["msg"][index]["value"]['contract']


def _execute_msgs(elem):
    out = []

    count = len(elem["tx"]["value"]["msg"])
    for i in range(count):
        out.append(_execute_msg(elem, i))
    return out


def _execute_msgs_keys(elem):
    msgs = _execute_msgs(elem)
    out = []
    for msg in msgs:
        keys = list(msg.keys())

        if len(keys) == 1:
            out.append(keys[0])
        else:
            out.append(None)
    return out


def _execute_msg(elem, index=0):
    msg_base64 = elem["tx"]["value"]["msg"][index]["value"]["execute_msg"]
    if type(msg_base64) is dict:
        return msg_base64

    msg = json.loads(base64.b64decode(msg_base64))

    for k, v in msg.items():
        if "msg" in v:
            msg[k]["msg"] = json.loads(base64.b64decode(v["msg"]))

    return msg


def _transfers(elem, wallet_address, txid, multicurrency=False):
    transfers_in = []
    transfers_out = []
    is_columbus_3 = (elem.get("chainId", None) == "columbus-3")
    if is_columbus_3:
        return _transfers_columbus_3(elem, wallet_address, txid, multicurrency)

    for log_index, log in enumerate(elem["logs"]):
        events = elem["logs"][log_index]["events"]

        for event in events:
            if event["type"] == "transfer":
                attributes = event["attributes"]

                for i in range(0, len(attributes), 3):
                    recipient = attributes[i]["value"]
                    sender = attributes[i + 1]["value"]
                    amount_string = attributes[i + 2]["value"]

                    if recipient == wallet_address:
                        if multicurrency:
                            for amount, currency in _amounts(amount_string):
                                transfers_in.append([amount, currency])
                        else:
                            amount, currency = _amount(amount_string)
                            transfers_in.append([amount, currency])
                    elif sender == wallet_address:
                        if multicurrency:
                            for amount, currency in _amounts(amount_string):
                                transfers_out.append([amount, currency])
                        else:
                            amount, currency = _amount(amount_string)
                            transfers_out.append([amount, currency])

    return transfers_in, transfers_out


def _transfers_columbus_3(elem, wallet_address, txid, multicurrency=False):
    transfers_in = []
    transfers_out = []

    for log_index, log in enumerate(elem["logs"]):
        events = elem["logs"][log_index]["events"]

        for event in events:
            if event["type"] == "transfer":
                attributes = event["attributes"]

                for i in range(0, len(attributes), 2):
                    recipient = attributes[i]["value"]
                    amount_string = attributes[i + 1]["value"]

                    if recipient == wallet_address:
                        if multicurrency:
                            for amount, currency in _amounts(amount_string):
                                transfers_in.append([amount, currency])
                        else:
                            amount, currency = _amount(amount_string)
                            transfers_in.append([amount, currency])
                    else:
                        if multicurrency:
                            for amount, currency in _amounts(amount_string):
                                transfers_out.append([amount, currency])
                        else:
                            amount, currency = _amount(amount_string)
                            transfers_out.append([amount, currency])

    return transfers_in, transfers_out


def _extract_amounts(amount_string):
    """
    Example input: '230344ukrw,3uluna,5umnt'
    Example output: { "KRW" : .0230344, "LUNA" : .000003, "MNT" : .00005 }
    """
    out = {}

    amounts = amount_string.split(",")
    for amount in amounts:
        if "terra" in amount:
            # token address (i.e. "766890terra1vxtwu4ehgzz77mnfwrntyrmgl64qjs75mpwqaz")
            uamount, partial_address = amount.split("terra")
            address = "terra{}".format(partial_address)
            currency, _ = _lookup_address(address, "")
            out[currency] = float(uamount) / MILLION
        elif "ibc" in amount:
            # ibc token (i.e. "165ibc/0471F1C4E7AFD3F07702BEF6DC365268D64570F7C1FDC98EA6098DD6DE59817B" for osmo)
            uamount, ibc_address = amount.split("ibc")
            ibc_address = "ibc" + ibc_address
            currency = _ibc_token_name(ibc_address)
            out[currency] = float(uamount) / MILLION
        else:
            # regular (i.e. 99700703uusd)
            uamount, currency = amount.split("u", 1)
            currency = _currency(currency)
            out[currency] = float(uamount) / MILLION

    return out


def _asset_to_currency(asset, txid):
    # Examples: terra1mqsjugsugfprn3cvgxsrr8akkvdxv2pzc74us7 -> 'uusd'
    if asset.startswith("terra"):
        currency, _ = _lookup_address(asset, txid)
        return currency

    if asset.startswith("u"):
        return _denom_to_currency(asset)

    raise Exception("_asset_to_currency(): Unable to determine currency for asset={} txid={}".format(
        asset, txid))


def _amounts(amounts_string):
    # Example inputs: '230344ukrw,3uluna,5umnt', '50674299uusd'
    out = []
    amounts = _extract_amounts(amounts_string)
    for currency, amount in amounts.items():
        out.append((amount, currency))

    return out


def _amount(amount_string):
    # Example input: '50674299uusd'

    amounts = _extract_amounts(amount_string)

    currency = list(amounts.keys())[0]
    amount = list(amounts.values())[0]
    return amount, currency


def _float_amount(amount_string, currency):
    # Example input: '50674299' , 'USD'
    if currency == CUR_ORION:
        return float(amount_string) / MILLION / 100
    else:
        return float(amount_string) / MILLION


def _currency(currency_string):
    currency_string = currency_string.upper()
    if currency_string == "KRW":
        return "KRT"
    if currency_string == "USD":
        return "UST"
    return currency_string


def _denom_to_currency(denom):
    currency = denom[1:]
    return _currency(currency)


# https://github.com/terra-project/shuttle
# https://github.com/terra-project/shuttle/blob/main/terra/src/config/TerraAssetInfos.ts
# https://lcd.terra.dev/swagger-ui/#/Wasm/get_wasm_contracts__contractAddress_
def _lookup_address(addr, txid):
    """ Returns (currency1, None) for currency address.
        Returns (currency1, currency2) for swap pair """
    if addr in localconfig.currency_addresses:
        return localconfig.currency_addresses[addr]

    init_msg = _query_wasm(addr)
    logging.info("init_msg: %s", init_msg)

    if "symbol" in init_msg:
        # Currency address
        currency = init_msg["symbol"]
        localconfig.currency_addresses[addr] = [currency, None]
        logging.info("Found symbol=%s ", currency)

        return [currency, None]
    elif "asset_infos" in init_msg:
        out = [None, None]

        # Swap contract pair address
        for i, asset_info in enumerate(init_msg["asset_infos"]):
            if "token" in asset_info:
                contract_addr = asset_info["token"]["contract_addr"]
                init_msg2 = _query_wasm(contract_addr)
                currency = init_msg2["symbol"]
                out[i] = currency
            elif "native_token" in asset_info:
                currency = _denom_to_currency(asset_info["native_token"]["denom"])
                out[i] = currency
            else:
                raise Exception("Unexpected data for asset_infos", addr, txid, init_msg)

        if out[0] is None or out[1] is None:
            raise Exception("Unable to determine swap pair", txid, init_msg)

        localconfig.currency_addresses[addr] = out
        return out
    elif "terraswap_factory" in init_msg:
        localconfig.currency_addresses[addr] = [None, None]
        return [None, None]

    localconfig.currency_addresses[addr] = ""
    raise Exception("Unable to determine currency/swap pair for addr=%s, txid=%s", addr, txid)


def _lookup_lp_address(addr, txid):
    if addr in localconfig.currency_addresses:
        return localconfig.currency_addresses[addr]

    init_msg = _query_wasm(addr)
    logging.info("init_msg: %s", init_msg)

    if "init_hook" in init_msg:
        address_pair = init_msg["init_hook"]["contract_addr"]
        currency1, currency2 = _lookup_address(address_pair, txid)
    elif "staking_token" in init_msg:
        staking_token = init_msg["staking_token"]
        init_msg = _query_wasm(staking_token)
        address_pair = init_msg["init_hook"]["contract_addr"]
        currency1, currency2 = _lookup_address(address_pair, txid)
    elif "mint" in init_msg:
        address_pair = init_msg["mint"]["minter"]
        currency1, currency2 = _lookup_address(address_pair, txid)
    else:
        raise Exception("Unable to determine lp currency for addr={}, txid={}".format(addr, txid))

    if currency1 == "UST":
        lp_currency = "LP_{}_UST".format(currency2)
        localconfig.currency_addresses[addr] = [lp_currency, None]
        return [lp_currency, None]
    elif currency2 == "UST":
        lp_currency = "LP_{}_UST".format(currency1)
        localconfig.currency_addresses[addr] = [lp_currency, None]
        return [lp_currency, None]
    elif currency1 and currency2:
        lp_currency = "LP_{}_{}".format(currency1, currency2)
        localconfig.currency_addresses[addr] = [lp_currency, None]
        return [lp_currency, None]
    else:
        localconfig.currency_addresses[addr] = ""
        raise Exception("Unable to determine lp currency for addr={}, txid={}".format(addr, txid))


def _query_wasm(addr):
    data = LcdAPI.contract_info(addr)

    init_msg = _init_msg(data)
    return init_msg


def _init_msg(data):
    init_msg_base64 = data["result"]["init_msg"]
    if type(init_msg_base64) is dict:
        return init_msg_base64

    init_msg = json.loads(base64.b64decode(init_msg_base64))
    return init_msg


def _ibc_token_name(address):
    # ibc/0471F1C4E7AFD3F07702BEF6DC365268D64570F7C1FDC98EA6098DD6DE59817B -> "OSMO"
    return IBC_TOKEN_NAMES.get(address, address)


def _event_with_action(elem, event_type, action):
    logs = elem["logs"]
    for log in logs:
        event = log["events_by_type"].get(event_type, None)
        if event:
            if action in event["action"]:
                return event
    return None


def _ingest_rows(exporter, rows, comment):
    for i, row in enumerate(rows):
        row.comment = comment
        if i > 0:
            row.fee, row.fee_currency = "", ""
        exporter.ingest_row(row)
