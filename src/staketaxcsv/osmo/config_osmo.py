from staketaxcsv.common import ExporterTypes as et
from staketaxcsv.common.config import config


class localconfig(config):

    # Treat LP deposits/withdrawals as "transfers"/"omit"/"trades" (ignored for koinly)
    lp_treatment = et.LP_TREATMENT_DEFAULT

    start_date = None
    end_date = None
    symbols = {}
    exponents = {}
    contracts = {}
