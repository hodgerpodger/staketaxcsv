"""
staketaxcsv

Details on usage:

    >>> import staketaxcsv
    >>> help(staketaxcsv.api)

Example usage:

    >>> import staketaxcsv
    >>>
    >>> address = "<SOME_ADDRESS>"
    >>> txid = "<SOME_TXID>"
    >>>
    >>> staketaxcsv.formats()
    ['default', 'balances', 'accointing', 'bitcointax', 'coinledger', 'coinpanda', 'cointelli', 'cointracking', 'cointracker', 'cryptio', 'cryptocom', 'cryptotaxcalculator', 'cryptoworth', 'koinly', 'recap', 'taxbit', 'tokentax', 'zenledger']
    >>>
    >>> staketaxcsv.tickers()
    ['ALGO', 'ATOM', 'BLD', 'BTSG', 'DVPN', 'EVMOS', 'FET', 'HUAHUA', 'IOTX', 'JUNO', 'KUJI', 'LUNA1', 'LUNA2', 'OSMO', 'REGEN', 'SOL', 'STARS']
    >>>
    >>> staketaxcsv.transaction("ATOM", address, txid, "koinly")
    ...
    >>> staketaxcsv.csv("ATOM", address, "koinly")
    ...
    >>> staketaxcsv.csv_all("ATOM", address)
    ...

"""

from .api import csv, csv_all, formats, tickers, transaction
