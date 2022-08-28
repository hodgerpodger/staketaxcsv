import logging
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
    wallet_address = None

    def __init__(self, wallet_address, msg_index, message, log, lcd_node, ibc_addresses):
        if lcd_node is not None:
            MsgInfoIBC.lcd_node = lcd_node
            MsgInfoIBC.ibc_addresses = ibc_addresses

        MsgInfoIBC.wallet_address = wallet_address
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
                        for amount, currency in self.amount_currency(amount_string):
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
                        for amount, currency in self.amount_currency(amount_string):
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
                        for amount, currency in self.amount_currency(amount_string):
                            if show_addrs:
                                transfers_in.append((amount, currency, sender, recipient))
                            else:
                                transfers_in.append((amount, currency))
                    elif sender == self.wallet_address:
                        for amount, currency in self.amount_currency(amount_string):
                            if show_addrs:
                                transfers_out.append((amount, currency, sender, recipient))
                            else:
                                transfers_out.append((amount, currency))
        return transfers_in, transfers_out

    def amount_currency(self, amount_string):
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

            # Convert from raw string to float amount and currency symbol
            amount, currency = MsgInfoIBC.amount_currency_from_raw(
                amount_raw, currency_raw, self.lcd_node, self.ibc_addresses)

            out.append((amount, currency))

        return out

    @staticmethod
    def amount_currency_from_raw(amount_raw, currency_raw, lcd_node, ibc_addresses):
        # example currency_raw:
        # 'ibc/B3504E092456BA618CC28AC671A71FB08C6CA0FD0BE7C8A5B5A3E2DD933CC9E4'
        # 'uluna'
        # 'aevmos'
        if currency_raw.startswith("ibc/"):
            # ibc address
            try:
                denom = common.ibc.api_lcd.ibc_address_to_denom(lcd_node, currency_raw, ibc_addresses)
                amount, currency = MsgInfoIBC._amount_currency_convert(amount_raw, denom)
                return amount, currency
            except Exception as e:
                logging.warning("Unable to find symbol for ibc address %s, exception=%s", currency_raw, str(e))
                amount = float(amount_raw) / co.MILLION
                return amount, currency_raw
        else:
            return MsgInfoIBC._amount_currency_convert(amount_raw, currency_raw)

    @staticmethod
    def _amount_currency_convert(amount_raw, currency_raw):
        # Special cases for nonconforming denoms/assets
        # currency_raw -> (currency, exponent)
        CURRENCY_RAW_MAP = {
            co.CUR_CRO : (co.CUR_CRO, 8),
            co.CUR_MOBX : (co.CUR_MOBX, 9),
            "gravity0xfB5c6815cA3AC72Ce9F5006869AE67f18bF77006" : (co.CUR_PSTAKE, 18),
            "OSMO": ("OSMO", 6),
            "osmo": ("OSMO", 6),
        }

        if currency_raw in CURRENCY_RAW_MAP:
            currency, exponent = CURRENCY_RAW_MAP[currency_raw]
            amount = float(amount_raw) / float(10 ** exponent)
            return amount, currency
        elif currency_raw.startswith("gamm/"):
            # osmosis lp currencies
            # i.e. "gamm/pool/6" -> "GAMM-6"
            amount = float(amount_raw) / co.EXP18
            _, _, num = currency_raw.split("/")
            currency = "GAMM-{}".format(num)
            return amount, currency
        elif currency_raw.endswith("-wei"):
            amount = float(amount_raw) / co.EXP18
            currency, _ = currency_raw.split("-wei")
            currency = currency.upper()
            return amount, currency
        elif currency_raw.startswith("a"):
            amount = float(amount_raw) / co.EXP18
            currency = currency_raw[1:].upper()
            return amount, currency
        elif currency_raw.startswith("nano"):
            amount = float(amount_raw) / co.EXP9
            currency = currency_raw[4:].upper()
            return amount, currency
        elif currency_raw.startswith("n"):
            amount = float(amount_raw) / co.EXP9
            currency = currency_raw[1:].upper()
            return amount, currency
        elif currency_raw.startswith("u"):
            amount = float(amount_raw) / co.MILLION
            currency = currency_raw[1:].upper()
            return amount, currency
        else:
            raise Exception("_amount_currency_from_raw(): no case for amount_raw={}, currency_raw={}".format(
                amount_raw, currency_raw))

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

                    if k in ["contract_address", "_contract_address"]:
                        # reached beginning of next action

                        # add previous action to list
                        if len(action):
                            actions.append(action)

                        # start new action
                        action = {}
                        action[k] = v
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
