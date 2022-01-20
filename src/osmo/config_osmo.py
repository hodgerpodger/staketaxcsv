class localconfig:

    job = None
    debug = False
    limit = None
    lp_transfers = False  # Treat LP deposits/withdrawals as transfers (default: treat as _LP_DEPOSIT/_LP_WITHDRAW)
    lp_trades = False     # Treat LP deposits/withdrawals as trades (default: treat as _LP_DEPOSIT/_LP_WITHDRAW)
    cache = False
    ibc_addresses = {}
