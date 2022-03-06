from common import ExporterTypes as et


class localconfig:

    job = None
    debug = False
    cache = False
    minor_rewards = False
    lp_treatment = et.LP_TREATMENT_DEFAULT  # Treat LP deposits/withdrawals as "transfers"/"omit"/"trades"
                                            # (ignored for koinly)
    limit = 10000                           # max txs

    # caches
    ibc_addresses = {}
    currency_addresses = {}  # <currency_address> -> <currency_symbol>
    decimals = {}  # <currency_symbol> -> <number_of_decimals>
    lp_currency_addresses = {}  # <lp_currency_address> -> <lp_currency_symbol>
