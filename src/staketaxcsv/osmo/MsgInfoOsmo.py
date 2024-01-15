import pprint

import staketaxcsv.common.ibc.constants as co
from staketaxcsv.osmo.api_osmosis import get_symbol, get_exponent
from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.osmo.config_osmo import localconfig


class MsgInfoOsmo(MsgInfoIBC):

    def __init__(self, wallet_address, msg_index, message, log, lcd_node, ibc_addresses):
        super().__init__(wallet_address, msg_index, message, log, lcd_node, ibc_addresses)
        self.events_by_type = self._events_by_type()

    def amount_currency_single(self, amount_raw, currency_raw):
        amount, currency = MsgInfoIBC.amount_currency_from_raw(
            amount_raw, currency_raw, self.lcd_node, self.ibc_addresses)

        if currency.startswith("unknown_"):
            # try osmosis api
            currency = self._symbol(currency_raw)
            if currency:
                exponent = self._exponent(currency)
                if exponent:
                    amount = float(amount_raw) / float(10 ** exponent)
                    return amount, currency

        return amount, currency

    def _symbol(self, denom):
        symbols = localconfig.symbols

        if denom in symbols:
            return symbols[denom]

        symbol = get_symbol(denom)

        symbols[denom] = symbol
        return symbol

    def _exponent(self, currency):
        exponents = localconfig.exponents

        if currency in exponents:
            return exponents[currency]

        exponent = get_exponent(currency)

        exponents[currency] = exponent
        return exponent
