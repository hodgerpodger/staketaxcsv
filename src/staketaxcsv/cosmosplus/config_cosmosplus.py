from staketaxcsv.common.config import config
from staketaxcsv.settings_csv import TICKER_COSMOSPLUS


class localconfig(config):

    node = ""
    ticker = TICKER_COSMOSPLUS
    mintscan_label = "generic"
    limit = 5000
