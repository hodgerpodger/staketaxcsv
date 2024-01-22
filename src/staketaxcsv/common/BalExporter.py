# Historical balances CSV

import csv
import logging
from tabulate import tabulate
BALANCES_HISTORICAL = "balances_historical"


class BalExporter:

    def __init__(self, wallet_address):
        self.wallet_address = wallet_address
        self.currencies_set = set()
        self.rows = []  # data rows info

    def currencies_list(self):
        return sorted(list(self.currencies_set))

    def ingest_row(self, timestamp, balances):
        """ Ingests single row, representing all token balances for a wallet at one timestamp.

        :param timestamp: YYYY-MM-DD HH:MM:SS
        :param balances: dict of <currency_ticker> -> <amount>
        """
        row = {
            "timestamp": timestamp,
            "balances": balances,
        }
        self.rows.append(row)

        # Update self.currencies
        for ticker, amount in balances.items():
            self.currencies_set.add(ticker)

    def _csv_header(self):
        return ["timestamp"] + self.currencies_list()

    def _csv_line(self, row, currencies):
        line = [
            row["timestamp"],
        ]

        for currency in currencies:
            amount = row["balances"].get(currency, "")
            line.append(amount)
        return line

    def export_csv(self, csvpath, reverse=True):
        self.rows.sort(key=lambda row: row["timestamp"], reverse=reverse)
        currencies = self.currencies_list()

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(self._csv_header())

            # data rows
            for row in self.rows:
                mywriter.writerow(self._csv_line(row, currencies))
        logging.info("Wrote to %s", csvpath)

    def export_for_test(self):
        # header row
        table = [self._csv_header()]

        # data rows
        currencies = self.currencies_list()
        for row in self.rows:
            table.append(self._csv_line(row, currencies))

        return tabulate(table)
