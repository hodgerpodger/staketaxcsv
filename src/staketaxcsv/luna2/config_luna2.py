from staketaxcsv.common.config import config


class localconfig(config):

    include_tiny_vesting = False

    # caches
    contracts = {}
    currency_addresses = {}
    lp_currency_addresses = {}
