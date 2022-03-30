from common import ExporterTypes as et


class localconfig:

    job = None
    debug = False
    limit = 30000  # max txs
    # Treat LP deposits/withdrawals as "transfers"/"omit"/"trades" (ignored for koinly)
    lp_treatment = et.LP_TREATMENT_DEFAULT
    cache = False

    ibc_addresses = {}
    exponents = {}
