import logging

import osmo.api_historical
from osmo.config_osmo import localconfig
from osmo.constants import CUR_CRO, EXP18, MILLION, MSG_TYPE_BEGIN_UNLOCKING, MSG_TYPE_LOCK_TOKENS


def _transfers(log, wallet_address):
    """
    Parses log element and returns (list of inbound transfers, list of outbound transfers),
    relative to wallet_address.
    """
    transfers_in = _transfers_coin_received(log, wallet_address)
    transfers_out = _transfers_coin_spent(log, wallet_address)

    if len(transfers_in) == 0 and len(transfers_out) == 0:
        # Only add "transfer" event if "coin_received"/"coin_spent" events do not exist
        transfers_in, transfers_out = _transfers_event(log, wallet_address)

    return transfers_in, transfers_out


def _transfers_coin_received(log, wallet_address):
    transfers_in = []

    events = log["events"]
    for event in events:
        event_type, attributes = event["type"], event["attributes"]

        if event_type == "coin_received":
            for i in range(0, len(attributes), 2):
                receiver = attributes[i]["value"]
                amount_string = attributes[i + 1]["value"]
                if receiver == wallet_address:
                    for amount, currency in _amount_currency(amount_string):
                        transfers_in.append((amount, currency))

    return transfers_in


def _transfers_coin_spent(log, wallet_address):
    transfers_out = []

    events = log["events"]
    for event in events:
        event_type, attributes = event["type"], event["attributes"]

        if event_type == "coin_spent":
            for i in range(0, len(attributes), 2):
                spender = attributes[i]["value"]
                amount_string = attributes[i + 1]["value"]
                if spender == wallet_address:
                    for amount, currency in _amount_currency(amount_string):
                        transfers_out.append((amount, currency))

    return transfers_out


def _transfers_event(log, wallet_address):
    transfers_in, transfers_out = [], []

    events = log["events"]
    for event in events:
        event_type, attributes = event["type"], event["attributes"]

        if event_type == "transfer":
            for i in range(0, len(attributes), 3):
                recipient = attributes[i]["value"]
                sender = attributes[i + 1]["value"]
                amount_string = attributes[i + 2]["value"]

                if recipient == wallet_address:
                    for amount, currency in _amount_currency(amount_string):
                        transfers_in.append((amount, currency))
                elif sender == wallet_address:
                    for amount, currency in _amount_currency(amount_string):
                        transfers_out.append((amount, currency))
    return transfers_in, transfers_out


def _amount_currency(amount_string):
    # i.e. "5000000uosmo",
    # i.e. "16939122ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E00EB64743EF4",
    # i.e. "899999999ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2,\
    #       1252125015450ibc/9712DBB13B9631EDFA9BF61B55F1B2D290B2ADB67E3A4EB3A875F3B6081B3B84"

    out = []
    for amt_string in amount_string.split(","):
        if "ibc" in amt_string:
            uamount, ibc_address = amt_string.split("ibc")

            ibc_address = "ibc" + ibc_address
            currency = _ibc_currency(ibc_address)
            amount = _amount(uamount, currency)
        elif "gamm" in amt_string:
            uamount, gamm_address = amt_string.split("gamm")

            gamm_address = "gamm" + gamm_address
            currency = _gamm_currency(gamm_address)
            amount = _amount(uamount, currency)
        elif "u" in amt_string:
            uamount, ucurrency = amt_string.split("u", 1)

            currency = ucurrency.upper()
            amount = _amount(uamount, currency)
        else:
            raise Exception("Unexpected amount_string: {}".format(amount_string))

        out.append((amount, currency))

    return out


def _amount(uamount, currency):
    if currency.startswith("GAMM-"):
        return float(uamount) / EXP18
    elif currency == CUR_CRO:
        return float(uamount) / MILLION / 100
    else:
        return float(uamount) / MILLION


def _denom_to_currency(denom):
    # i.e. "uosmo"
    return denom[1:].upper()


class NoSymbol:

    ibc_addresses = set()


def _ibc_currency(ibc_address):
    # i.e. "ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E00EB64743EF4" -> "IKT"
    if ibc_address in localconfig.ibc_addresses:
        return localconfig.ibc_addresses[ibc_address]

    result = osmo.api_historical.get_symbol(ibc_address)
    val = result if result else ibc_address

    localconfig.ibc_addresses[ibc_address] = val
    return val


def _gamm_currency(gamm_address):
    # i.e. "gamm/pool/6"
    _, _, num = gamm_address.split("/")
    return "GAMM-{}".format(num)


def _msg_type(msginfo):
    # i.e. /osmosis.lockup.MsgBeginUnlocking -> _MsgBeginUnlocking
    last_field = msginfo.message["@type"].split(".")[-1]
    return last_field


def _make_tx_type(msginfo):
    msg_type = _msg_type(msginfo)
    return "_" + msg_type


def _ingest_rows(exporter, rows, comment):
    for i, row in enumerate(rows):
        row.comment = comment
        if i > 0:
            row.fee, row.fee_currency = "", ""
        exporter.ingest_row(row)


def _period_lock_id(msginfo):
    msg_index = msginfo.msg_index
    log = msginfo.log
    msg_type = _msg_type(msginfo)

    # Determine type to lookup when parsing events
    if msg_type == MSG_TYPE_LOCK_TOKENS:
        event_type_target = "lock_tokens"
    elif msg_type == MSG_TYPE_BEGIN_UNLOCKING:
        event_type_target = "begin_unlock"
    else:
        logging.critical("_period_lock_id(): Unexpected msg_type=%s", msg_type)
        return ""

    # Extract period_lock_id value from events
    for event in log["events"]:
        event_type = event["type"]
        attributes = event["attributes"]

        if event_type == event_type_target:
            for kv in attributes:
                k, v = kv["key"], kv["value"]
                if k == "period_lock_id":
                    return v

    logging.error("Unable to find period_lock_id for msg_index=%s", msg_index)
