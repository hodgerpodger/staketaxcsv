import staketaxcsv.common.ibc.constants as co
import staketaxcsv.osmo.api_historical
from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.osmo.config_osmo import localconfig


class MsgInfoOsmo(MsgInfoIBC):

    def amount_float(self, amount_string, currency):
        if currency == co.CUR_CRO:
            return float(amount_string) / co.MILLION / 100
        elif currency in [co.CUR_FET, co.CUR_EVMOS]:
            return float(amount_string) / co.EXP18
        elif currency == co.CUR_MOBX:
            return float(amount_string) / co.EXP9
        elif currency.startswith("GAMM-"):
            return float(amount_string) / co.EXP18
        else:
            return float(amount_string) / float(10 ** self._exponent(currency))

    def _exponent(self, currency):
        if currency in localconfig.exponents:
            return int(localconfig.exponents[currency])

        exponent = staketaxcsv.osmo.api_historical.get_exponent(currency)
        if exponent is None:
            exponent = 6

        localconfig.exponents[currency] = exponent
        return int(localconfig.exponents[currency])
