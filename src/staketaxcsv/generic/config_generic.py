from staketaxcsv.common.config import config
from staketaxcsv.settings_csv import TICKER_GENERIC


class localconfig(config):

    ibc_addresses = {}

    node = ""
    ticker = TICKER_GENERIC
    mintscan_label = "generic"
