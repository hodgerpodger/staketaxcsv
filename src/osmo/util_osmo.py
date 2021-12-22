
from osmo.constants import MILLION
from osmo.tickers.tickers import TickersIBC
from osmo.MyWallets import MyWallets


def _transfers(log, wallet_address):
    """
    Parses log element and returns (list of inbound transfers, list of outbound transfers),
    relative to wallet_address.
    """
    wallet_addresses = MyWallets.get(wallet_address)

    transfers_in = _transfers_coin_received(log, wallet_addresses)
    transfers_out = _transfers_coin_spent(log, wallet_addresses)

    if len(transfers_in) == 0 and len(transfers_out) == 0:
        # Only add "transfer" event if "coin_received"/"coin_spent" events do not exist
        transfers_in, transfers_out = _transfers_event(log, wallet_addresses)

    return transfers_in, transfers_out


def _transfers_coin_received(log, wallet_addresses):
    transfers_in = []

    events = log["events"]
    for event in events:
        event_type, attributes = event["type"], event["attributes"]

        if event_type == "coin_received":
            for i in range(0, len(attributes), 2):
                receiver = attributes[i]["value"]
                amount_string = attributes[i + 1]["value"]
                if receiver in wallet_addresses:
                    amount, currency = _amount_currency(amount_string)
                    transfers_in.append((amount, currency))

    return transfers_in


def _transfers_coin_spent(log, wallet_addresses):
    transfers_out = []

    events = log["events"]
    for event in events:
        event_type, attributes = event["type"], event["attributes"]

        if event_type == "coin_spent":
            for i in range(0, len(attributes), 2):
                spender = attributes[i]["value"]
                amount_string = attributes[i + 1]["value"]
                if spender in wallet_addresses:
                    amount, currency = _amount_currency(amount_string)
                    transfers_out.append((amount, currency))

    return transfers_out


def _transfers_event(log, wallet_addresses):
    transfers_in, transfers_out = [], []

    events = log["events"]
    for event in events:
        event_type, attributes = event["type"], event["attributes"]

        if event_type == "transfer":
            for i in range(0, len(attributes), 3):
                recipient = attributes[i]["value"]
                sender = attributes[i + 1]["value"]
                amount_string = attributes[i + 2]["value"]

                if recipient in wallet_addresses:
                    amount, currency = _amount_currency(amount_string)
                    transfers_in.append((amount, currency))
                elif sender in wallet_addresses:
                    amount, currency = _amount_currency(amount_string)
                    transfers_out.append((amount, currency))
    return transfers_in, transfers_out


def _amount_currency(amount_string):
    # i.e. "5000000uosmo",
    # "16939122ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E00EB64743EF4",
    if "ibc" in amount_string:
        uamount, ibc_address = amount_string.split("ibc")

        ibc_address = "ibc" + ibc_address
        currency = _ibc_currency(ibc_address)
        amount = _amount(uamount, currency)

        return amount, currency
    elif "u" in amount_string:
        uamount, ucurrency = amount_string.split("u", 1)
        currency = ucurrency.upper()
        amount = _amount(uamount, currency)

        return amount, currency


def _amount(uamount, currency):
    return float(uamount) / MILLION


def _denom_to_currency(denom):
    # i.e. "uosmo"
    return denom[1:].upper()


def _ibc_currency(ibc_address):
    # i.e. "ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E00EB64743EF4" -> "IKT"
    result = TickersIBC.lookup(ibc_address)
    if result:
        return result
    else:
        return ibc_address


