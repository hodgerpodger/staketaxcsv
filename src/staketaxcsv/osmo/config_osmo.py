from staketaxcsv.common import ExporterTypes as et
from staketaxcsv.common.config import config


class localconfig(config):

    limit = 30000  # max txs
    # Treat LP deposits/withdrawals as "transfers"/"omit"/"trades" (ignored for koinly)
    lp_treatment = et.LP_TREATMENT_DEFAULT

    ibc_addresses = {}
    exponents = {}
