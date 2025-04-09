from staketaxcsv.common.config import config
from staketaxcsv.settings_csv import TICKER_COSMOSPLUS2
from staketaxcsv.settings_csv import MINTSCAN_MAX_TXS


class localconfig(config):

    node = ""
    ticker = TICKER_COSMOSPLUS2
    mintscan_label = "generic"

    start_date = None
    end_date = None
    limit = MINTSCAN_MAX_TXS
