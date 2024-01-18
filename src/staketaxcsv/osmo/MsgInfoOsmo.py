import pprint

from staketaxcsv.osmo.api_osmosis import get_symbol, get_exponent
from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.osmo import denoms as denoms_osmo
from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.common.ibc import denoms
from staketaxcsv.osmo import denoms as denoms_osmo


class MsgInfoOsmo(MsgInfoIBC):

    def __init__(self, wallet_address, msg_index, message, log, lcd_node):
        super().__init__(wallet_address, msg_index, message, log, lcd_node)
        self.events_by_type = self._events_by_type()

    def amount_currency_single(self, amount_raw, currency_raw):
        return denoms_osmo.amount_currency_from_raw(amount_raw, currency_raw, self.lcd_node)

    # def amount_currency_single(self, amount_raw, currency_raw):
    #     amount, currency = denoms.amount_currency_from_raw(
    #         amount_raw, currency_raw, self.lcd_node)
    #
    #     if currency.startswith("unknown_"):
    #         # try osmosis api
    #         currency = denoms_osmo.symbol(currency_raw)
    #         if currency:
    #             exponent = denoms_osmo.exponent(currency)
    #             if exponent:
    #                 amount = float(amount_raw) / float(10 ** exponent)
    #                 return amount, currency
    #
    #     return amount, currency
