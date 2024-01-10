from staketaxcsv.common.config import config
from staketaxcsv.settings_csv import MINTSCAN_MAX_TXS


class localconfig(config):

    ibc_addresses = {}
    start_date = None
    end_date = None
    limit = MINTSCAN_MAX_TXS
