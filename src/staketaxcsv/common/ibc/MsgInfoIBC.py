import logging
import pprint
import re
import base64

import staketaxcsv.common.ibc.constants as co
from staketaxcsv.common.ibc import util_ibc, denoms

COIN_RECEIVED = "coin_received"
COIN_SPENT = "coin_spent"
RECEIVER = "receiver"
SPENDER = "spender"
AMOUNT = "amount"


class MsgInfoIBC:
    """ Single message info for index <i> """

    lcd_node = None
    wallet_address = None

    def __init__(self, wallet_address, msg_index, message, log, lcd_node):
        if lcd_node is not None:
            MsgInfoIBC.lcd_node = lcd_node

        MsgInfoIBC.wallet_address = wallet_address
        self.msg_index = msg_index
        self.message = message
        self.msg_type = self._msg_type(message)
        self.log = log
        self.transfers = self._transfers()
        self.transfers_net = util_ibc.aggregate_transfers_net(self.transfers[0], self.transfers[1])
        self.transfers_event = self._transfers_transfer_event(show_addrs=True)
        self.wasm = MsgInfoIBC.wasm(log)
        self.contract = self._contract(message)
        self.events_by_type = self._events_by_type()

    def print(self):
        print("\nmsg{}:".format(self.msg_index))
        print("\tmsg_type: {}".format(self.msg_type))
        print("\tcontract: {}".format(self.contract))
        print("\ttransfers_in: {}".format(self.transfers[0]))
        print("\ttransfers_out: {}".format(self.transfers[1]))
        print("\ttransfers_net_in: {}".format(self.transfers_net[0]))
        print("\ttransfers_net_out: {}".format(self.transfers_net[1]))
        print("\n\tmessage:")
        pprint.pprint(self.message)
        print("\n\twasm:")
        pprint.pprint(self.wasm)
        print("\n\tevents_by_type:")
        pprint.pprint(self.events_by_type)

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

    def _num_keys(self, attributes):
        return len(set([a["key"] for a in attributes]))

    def _transfers_coin_received(self):
        transfers_in = []

        events = self.log["events"]
        for event in events:
            event_type, attributes = event["type"], event["attributes"]

            # In rare cases, base64 decode required.
            self._handle_base64_attributes(attributes)

            if event_type == COIN_RECEIVED:
                # Remove authz_msg_index key/values (if exists) so that uniform logic afterwards is consistent.
                attributes = self._remove_authz_msg_index(attributes)

                for i in range(0, len(attributes), self._num_keys(attributes)):
                    first_key = attributes[i]["key"]

                    if first_key == AMOUNT:
                        # Special case in JUNO only as of 10/4/2022
                        amount_string = attributes[i]["value"]
                        receiver = attributes[i + 1]["value"]
                    elif first_key == RECEIVER:
                        receiver = attributes[i]["value"]
                        amount_string = attributes[i + 1].get("value", "")
                    else:
                        raise Exception("Unexpected format in coin_received event")

                    if receiver == self.wallet_address:
                        for amount, currency in self.amount_currency(amount_string):
                            transfers_in.append((amount, currency))

        return transfers_in

    def _handle_base64_attributes(self, attributes):
        # In rare cases, base64 decode required for elements under attributes
        if len(attributes) > 0 and "index" in attributes[0]:
            try:
                for attr in attributes:
                    if "key" in attr:
                        attr["key"] = base64.b64decode(attr["key"]).decode()
                    if "value" in attr:
                        attr["value"] = base64.b64decode(attr["value"]).decode()
            except Exception as e:
                pass

    def _remove_authz_msg_index(self, attributes):
        out = []
        for kv in attributes:
            if kv["key"] == "authz_msg_index":
                continue
            out.append(kv)
        return out

    def _transfers_coin_spent(self):
        transfers_out = []

        events = self.log["events"]
        for event in events:
            event_type, attributes = event["type"], event["attributes"]

            # In rare cases, base64 decode required.
            self._handle_base64_attributes(attributes)

            if event_type == COIN_SPENT:
                # Remove authz_msg_index key/values (if exists) so that uniform logic afterwards is consistent.
                attributes = self._remove_authz_msg_index(attributes)

                for i in range(0, len(attributes), self._num_keys(attributes)):
                    first_key = attributes[i]["key"]

                    if first_key == AMOUNT:
                        # Special case in JUNO only as of 10/4/2022
                        amount_string = attributes[i]["value"]
                        spender = attributes[i + 1]["value"]
                    elif first_key == SPENDER:
                        spender = attributes[i]["value"]
                        amount_string = attributes[i + 1].get("value", "")
                    else:
                        raise Exception("Unexpected format in coin_spent event")

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

            # In rare cases, base64 decode required.
            self._handle_base64_attributes(attributes)

            if event_type == "transfer":
                # ignore MsgMultiSend case (uses different format)
                if self.msg_type == co.MSG_TYPE_MULTI_SEND:
                    continue

                # Prevent crash in weird data where key="authz_msg_index" for last 2 attributes
                if (len(attributes) > 1
                     and attributes[-1]["key"] == "authz_msg_index"
                     and attributes[-2]["key"] == "authz_msg_index"):
                    attributes.pop()

                # Handle all other cases
                for i in range(0, len(attributes), self._num_keys(attributes)):
                    first_key = attributes[i]["key"]

                    if first_key == AMOUNT:
                        # Special case in JUNO only as of 10/4/2022
                        amount_string = attributes[i]["value"]
                        recipient = attributes[i + 1]["value"]
                        sender = attributes[i + 2]["value"]
                    else:
                        recipient = attributes[i]["value"]
                        sender = attributes[i + 1]["value"]
                        amount_string = attributes[i + 2].get("value", "")

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

            amount, currency = self.amount_currency_single(amount_raw, currency_raw)

            out.append((amount, currency))

        return out

    def amount_currency_single(self, amount_raw, currency_raw):
        # Convert from raw string to float amount and currency symbol
        amount, currency = denoms.amount_currency_from_raw(amount_raw, currency_raw, self.lcd_node)
        return amount, currency

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

    def _events_by_type(self):
        log = self.log

        out = {}
        for event in log["events"]:
            attributes = event["attributes"]
            event_type = event["type"]

            if event_type not in out:
                out[event_type] = {}

            for attribute in attributes:
                k, v = str(attribute.get("key")), str(attribute.get("value"))

                if k in out[event_type]:
                    out[event_type][k] += "," + v
                else:
                    out[event_type][k] = v
        return out
