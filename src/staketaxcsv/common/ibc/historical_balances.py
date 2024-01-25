from staketaxcsv.common.ibc.api_mintscan_v1 import get_balances_all
from staketaxcsv.common.BalExporter import BalExporter
from collections import defaultdict
from dateutil import parser
from staketaxcsv.common.ibc import denoms
from staketaxcsv.osmo import denoms as denoms_osmo
from staketaxcsv.settings_csv import TICKER_OSMO
from staketaxcsv.common.ibc.api_lcd import make_lcd_api
TINY_AMOUNT = .00001


def via_mintscan(lcd_node, ticker, address, max_txs, start_date=None, end_date=None):
    exporter = BalExporter(address)

    # Get native staking denom (to use for unbonding section)
    bond_denom = make_lcd_api(lcd_node).get_bond_denom()

    entries = get_balances_all(ticker, address, max_txs, start_date, end_date)
    for entry in entries:
        timestamp = parser.parse(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        balance = defaultdict(int)

        # Process "bank" section
        for item in entry["bank"]:
            denom = item["denom"]
            amount_raw = int(item["amount"])
            amount, currency = _amount_currency(amount_raw, denom, lcd_node, ticker)

            balance[currency] += amount

        # Process "delegation" section
        for item in entry["delegation"]:
            denom = item["balance"]["denom"]
            amount_raw = int(item["balance"]["amount"])
            amount, currency = _amount_currency(amount_raw, denom, lcd_node, ticker)

            balance[currency] += amount

        # Process "unbonding" section
        for item in entry["unbonding"]:
            for subitem in item["entries"]:
                denom = bond_denom
                amount_raw = int(subitem["balance"])
                amount, currency = _amount_currency(amount_raw, denom, lcd_node, ticker)

                balance[currency] += amount

        # Process "reward" section
        for item in entry["reward"]:
            for subitem in item["reward"]:
                denom = subitem["denom"]
                amount_raw = float(subitem["amount"])
                amount, currency = _amount_currency(amount_raw, denom, lcd_node, ticker)

                balance[currency] += amount

        # omit currencies with super tiny amounts
        balance_edited = {}
        for currency, amount in balance.items():
            if amount < TINY_AMOUNT:
                continue
            balance_edited[currency] = amount

        # Ingest the summed balances into the exporter
        exporter.ingest_row(timestamp, balance_edited)

    return exporter


def _amount_currency(amount_raw, denom, lcd_node, ticker):
    if ticker == TICKER_OSMO:
        return denoms_osmo.amount_currency_from_raw(amount_raw, denom, lcd_node)
    else:
        return denoms.amount_currency_from_raw(amount_raw, denom, lcd_node)
