from staketaxcsv.common.config import config


class localconfig(config):

    limit = 10000               # max txs
    start_date = None
    end_date = None
    exclude_failed = False      # exclude failed transactions
    exclude_associated = False  # exclude associated token accounts' transactions
