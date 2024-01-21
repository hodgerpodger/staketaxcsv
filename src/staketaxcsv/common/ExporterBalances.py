# Historical balances CSV

import csv
import logging
BALANCES_HISTORICAL = "balances_historical"


class ExporterBalances:

    def __init__(self, wallet_address):
        self.wallet_address = wallet_address
        self.currencies_set = set()
        self.rows = []

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

    def csv(self, csvpath, reverse=True):
        self.rows.sort(key=lambda row: row["timestamp"], reverse=reverse)
        currencies = self.currencies_list()

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(["timestamp"] + self.currencies_list())

            # data rows
            for row in self.rows:
                line = [
                    row["timestamp"],
                ]

                for currency in currencies:
                    amount = row["balances"].get(currency, "")
                    line.append(amount)

                mywriter.writerow(line)
        logging.info("Wrote to %s", csvpath)

