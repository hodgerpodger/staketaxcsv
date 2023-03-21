from staketaxcsv.common.config import config
from staketaxcsv.settings_csv import TICKER_COSMOSPLUS


class localconfig(config):

    ibc_addresses = {}

    node = ""
    ticker = TICKER_COSMOSPLUS
    mintscan_label = "generic"
