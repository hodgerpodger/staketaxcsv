class localconfig:

    job = None
    debug = False
    cache = False
    minor_rewards = False
    lp_transfers = False     # Treat LP deposits/withdrawals as transfers (default: treat as _LP_DEPOSIT/_LP_WITHDRAW)
    lp_trades = False        # Treat LP deposits/withdrawals as trades (default: treat as _LP_DEPOSIT/_LP_WITHDRAW)
    limit = None

    # caches
    ibc_addresses = {}
    currency_addresses = {}  # <currency_address> -> <currency_symbol>
    decimals = {}  # <currency_symbol> -> <number_of_decimals>
    lp_currency_addresses = {}  # <lp_currency_address> -> <lp_currency_symbol>
