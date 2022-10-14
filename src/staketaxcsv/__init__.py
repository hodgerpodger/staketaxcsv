"""
staketaxcsv

Example usage:

    >>> import staketaxcsv
    >>> help(staketaxcsv.api)
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
    >>> # write single transaction CSV
    >>> staketaxcsv.transaction("ATOM", address, txid, "koinly")
    ...
    >>> # write koinly CSV
    >>> staketaxcsv.csv("ATOM", address, "koinly")
    ...
    >>> # write all CSVs (koinly, cointracking, etc.)
    >>> staketaxcsv.csv_all("ATOM", address)
    ...
    >>> # check address is valid
    >>> staketaxcsv.has_csv("ATOM", address)
    True

"""

from .api import csv, csv_all, formats, tickers, transaction, has_csv
