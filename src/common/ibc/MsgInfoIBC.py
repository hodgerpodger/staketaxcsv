import re

import common.ibc.api_lcd
import common.ibc.constants as co
import common.ibc.util_ibc


COIN_RECEIVED = "coin_received"
COIN_SPENT = "coin_spent"


class MsgInfoIBC:
    """ Single message info for index <i> """

    lcd_node = None
    ibc_addresses = None

    def __init__(self, wallet_address, msg_index, message, log, lcd_node, ibc_addresses):
        if lcd_node is None:
            MsgInfoIBC.lcd_node = lcd_node
            MsgInfoIBC.ibc_addresses = ibc_addresses

        self.wallet_address = wallet_address
        self.msg_index = msg_index
        self.message = message
        self.msg_type = self._msg_type(message)
        self.log = log
        self.transfers = self._transfers()
        self.transfers_event = self._transfers_transfer_event(show_addrs=True)
        self.wasm = MsgInfoIBC.wasm(log)
        self.contract = self._contract(message)

    def _msg_type(self, message):
        if "@type" in message:
            # i.e. /osmosis.lockup.MsgBeginUnlocking -> _MsgBeginUnlocking
            last_field = message["@type"].split(".")[-1]
        elif "type" in message:
            # luna2 only: staking/MsgUndelegate -> MsgUndelegate
            last_field = message["type"].split("/")[-1]
        else:
            raise Exception("Unexpected message: {}".format(message))
        return last_field

    def _has_coin_spent_received(self):
        return self._has_event_type(COIN_SPENT) and self._has_event_type(COIN_SPENT)

    def _transfers(self):
        """
        Parses log element and returns (list of inbound transfers, list of outbound transfers),
        relative to wallet_address.
        """
        transfers_in = self._transfers_coin_received()
        transfers_out = self._transfers_coin_spent()

        if not self._has_coin_spent_received():
            # Only add "transfer" event if "coin_received"/"coin_spent" events do not exist
            transfers_in, transfers_out = self._transfers_transfer_event()

        return transfers_in, transfers_out

    def _has_event_type(self, target_event_type):
        events = self.log["events"]
        for event in events:
            event_type, attributes = event["type"], event["attributes"]
            if event_type == target_event_type:
                return True
        return False

    def _transfers_coin_received(self):
        transfers_in = []

        events = self.log["events"]
        for event in events:
            event_type, attributes = event["type"], event["attributes"]

            if event_type == COIN_RECEIVED:
                for i in range(0, len(attributes), 2):
                    receiver = attributes[i]["value"]
                    amount_string = attributes[i + 1]["value"]
                    if receiver == self.wallet_address:
                        for amount, currency in MsgInfoIBC.amount_currency(amount_string):
                            transfers_in.append((amount, currency))

        return transfers_in

    def _transfers_coin_spent(self):
        transfers_out = []

        events = self.log["events"]
        for event in events:
            event_type, attributes = event["type"], event["attributes"]

            if event_type == COIN_SPENT:
                for i in range(0, len(attributes), 2):
                    spender = attributes[i]["value"]
                    amount_string = attributes[i + 1]["value"]

                    if spender == self.wallet_address:
                        for amount, currency in MsgInfoIBC.amount_currency(amount_string):
                            transfers_out.append((amount, currency))

        return transfers_out

    def _transfers_transfer_event(self, show_addrs=False):
        """ Returns (list of inbound transfers, list of outbound transfers), relative to wallet_address
            using transfer event element only. """
        transfers_in, transfers_out = [], []

        events = self.log["events"]
        for event in events:
            event_type, attributes = event["type"], event["attributes"]

            if event_type == "transfer":
                # ignore MsgMultiSend case (uses different format)
                if self.msg_type == co.MSG_TYPE_MULTI_SEND:
                    continue

                # Handle all other cases
                for i in range(0, len(attributes), 3):
                    recipient = attributes[i]["value"]
                    sender = attributes[i + 1]["value"]
                    amount_string = attributes[i + 2]["value"]

                    if recipient == self.wallet_address:
                        for amount, currency in MsgInfoIBC.amount_currency(amount_string):
                            if show_addrs:
                                transfers_in.append((amount, currency, sender, recipient))
                            else:
                                transfers_in.append((amount, currency))
                    elif sender == self.wallet_address:
                        for amount, currency in MsgInfoIBC.amount_currency(amount_string):
                            if show_addrs:
                                transfers_out.append((amount, currency, sender, recipient))
                            else:
                                transfers_out.append((amount, currency))
        return transfers_in, transfers_out

    @classmethod
    def amount_currency(cls, amount_string):
        # i.e. "5000000uosmo",
        # i.e. "16939122ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E00EB64743EF4",
        # i.e. "899999999ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2,\
        #       1252125015450ibc/9712DBB13B9631EDFA9BF61B55F1B2D290B2ADB67E3A4EB3A875F3B6081B3B84"
        out = []
        for amt_string in amount_string.split(","):
            if amt_string == "":
                continue

            # Split into (amount_raw, currency_raw)
            m = re.search('^(\d+)(.*)', amt_string)
            if not m:
                raise Exception("Unexpected amt_string: {}".format(amt_string))
            amount_raw, currency_raw = m.group(1), m.group(2)

            # Determine final (amount, currency)
            if "ibc/" in currency_raw:
                currency = cls.ibc_symbol(currency_raw)
                amount = cls.amount(amount_raw, currency)
            else:
                amount, currency = cls._amount_currency_from_raw(amount_raw, currency_raw)

            out.append((amount, currency))

        return out

    @classmethod
    def amount(cls, amount_string, currency):
        if currency == co.CUR_CRO:
            return float(amount_string) / co.MILLION / 100
        elif currency in [co.CUR_FET, co.CUR_EVMOS]:
            return float(amount_string) / co.EXP18
        elif currency == co.CUR_MOBX:
            return float(amount_string) / co.EXP9
        else:
            return float(amount_string) / co.MILLION

    @classmethod
    def _amount_currency_from_raw(cls, amount_raw, currency_raw):
        # i.e. 2670866451930aevmos
        if currency_raw.startswith("a"):
            amount = float(amount_raw) / co.EXP18
            currency = currency_raw[1:].upper()
            return amount, currency
        elif currency_raw.startswith("nano"):
            amount = float(amount_raw) / co.EXP9
            currency = currency_raw[4:].upper()
            return amount, currency
        elif currency_raw.startswith("u"):
            amount = float(amount_raw) / co.MILLION
            currency = currency_raw[1:].upper()
            return amount, currency
        else:
            raise Exception("_amount_currency_from_raw(): no case for amount_raw={}, currency_raw={}".format(
                amount_raw, currency_raw))

    @classmethod
    def denom_to_currency(cls, denom):
        # Example: 'uluna' -> 'LUNA'
        if denom.startswith("u") or denom.startswith("a"):
            return denom[1:].upper()
        else:
            raise Exception("Unexpected denom={}".format(denom))

    @classmethod
    def ibc_symbol(cls, ibc_address):
        # i.e. "ibc/1480B8FD20AD5FCAE81EA87584D269547DD4D436843C1D20F15E00EB64743EF4" -> "IKT"
        if not cls.lcd_node:
            return ibc_address
        if ibc_address in cls.ibc_addresses:
            return cls.ibc_addresses[ibc_address]

        result = common.ibc.api_lcd.get_ibc_ticker(cls.lcd_node, ibc_address, cls.ibc_addresses)
        val = result if result else ibc_address

        cls.ibc_addresses[ibc_address] = val
        return val

    @classmethod
    def wasm(cls, log):
        """ Parses wasm in log to return list of action dictionaries. """

        events = log["events"]
        for event in events:
            attributes, event_type = event["attributes"], event["type"]

            if event_type == "wasm":
                actions = []
                action = {}

                for kv in attributes:
                    k, v = kv["key"], kv["value"]

                    if k == "contract_address":
                        # reached beginning of next action

                        # add previous action to list
                        if len(action):
                            actions.append(action)

                        # start new action
                        action = {}
                        action["contract_address"] = v
                    else:
                        action[k] = v

                if len(action):
                    actions.append(action)
                return actions

        return []

    def _contract(self, message):
        if message and "contract" in message:
            return message["contract"]
        else:
            return None
