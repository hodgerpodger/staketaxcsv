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

    def _msg_type(self, message):
        # i.e. /osmosis.lockup.MsgBeginUnlocking -> _MsgBeginUnlocking
        last_field = message["@type"].split(".")[-1]
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
            if "ibc/" in amt_string:
                uamount, ibc_address = amt_string.split("ibc/")

                ibc_address = "ibc/" + ibc_address
                currency = cls.ibc_symbol(ibc_address)
                amount = cls.amount(uamount, currency)
            elif "u" in amt_string:
                uamount, ucurrency = amt_string.split("u", 1)

                currency = ucurrency.upper()
                amount = cls.amount(uamount, currency)
            elif "afet" in amt_string:
                uamount, ucurrency = amt_string.split("afet", 1)
                currency = "FET"
                amount = cls.amount(uamount, currency)
            else:
                raise Exception("Unexpected amount_string: {}".format(amount_string))

            out.append((amount, currency))

        return out

    @classmethod
    def amount(cls, uamount, currency):
        if currency == co.CUR_CRO:
            return float(uamount) / co.MILLION / 100
        elif currency == co.CUR_FET:
            return float(uamount) / co.EXP18
        else:
            return float(uamount) / co.MILLION

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
