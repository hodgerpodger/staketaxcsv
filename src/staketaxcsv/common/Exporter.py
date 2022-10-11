import csv
import io
import logging
import time
from datetime import datetime

import pandas as pd
import pytz
from pytz import timezone
from staketaxcsv.common import ExporterTypes as et
from staketaxcsv.common.exporter_koinly import NullMap
from staketaxcsv.settings_csv import TICKER_ALGO, TICKER_ATOM, TICKER_LUNA1, TICKER_LUNA2
from tabulate import tabulate


class Row:

    def __init__(self, timestamp, tx_type, received_amount, received_currency, sent_amount, sent_currency, fee,
                 fee_currency, exchange, wallet_address, txid, url="", z_index=0, comment=""):
        self.timestamp = timestamp
        self.tx_type = tx_type
        self.received_amount = self._format_amount(received_amount)
        self.received_currency = self._format_currency(received_currency)
        self.sent_amount = self._format_amount(sent_amount)
        self.sent_currency = self._format_currency(sent_currency)
        self.fee = self._format_amount(fee)
        self.fee_currency = fee_currency
        self.exchange = exchange
        self.wallet_address = wallet_address
        self.txid = txid
        self.url = url
        self.z_index = z_index  # Determines ordering for rows with same txid
        self.comment = comment

    def _format_currency(self, currency):
        if currency == "BLUNA":
            return "bLUNA"
        return currency

    def _format_amount(self, amount):
        """ Avoid scientific notation """
        if amount is None or amount == "":
            return ""
        elif float(amount) == 0:
            return 0
        elif float(amount) < .001:
            return "{:.9f}".format(float(amount))
        else:
            return amount

    def as_array(self):
        return [
            self.timestamp,
            self.tx_type,
            self.received_amount,
            self.received_currency,
            self.sent_amount,
            self.sent_currency,
            self.fee,
            self.fee_currency,
            self.comment,
            self.txid,
            self.url,
            self.exchange,
            self.wallet_address,
        ]

    def as_array_short(self):
        return [
            self.timestamp,
            self.tx_type,
            self.received_amount,
            self.received_currency,
            self.sent_amount,
            self.sent_currency,
            self.fee,
            self.fee_currency,
            self.txid
        ]


class Exporter:

    def __init__(self, wallet_address, localconfig=None, ticker=""):
        self.wallet_address = wallet_address
        self.rows = []
        self.is_reverse = None  # last sorted direction
        self.ticker = ticker
        self.koinly_nullmap = NullMap(localconfig)
        if localconfig and hasattr(localconfig, "lp_treatment") and localconfig.lp_treatment:
            self.lp_treatment = localconfig.lp_treatment
        else:
            self.lp_treatment = et.LP_TREATMENT_DEFAULT

    def ingest_row(self, row):
        self.rows.append(row)

    def ingest_csv(self, default_csv):
        """ Loads default csv file into self.rows """
        with open(default_csv, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                cur_row = Row(
                    timestamp=row["timestamp"],
                    tx_type=row["tx_type"],
                    received_amount=row["received_amount"],
                    received_currency=row["received_currency"],
                    sent_amount=row["sent_amount"],
                    sent_currency=row["sent_currency"],
                    fee=row["fee"],
                    fee_currency=row["fee_currency"],
                    exchange=row["exchange"],
                    wallet_address=row["wallet_address"],
                    txid=row["txid"],
                    url=row["url"],
                    z_index=-i,
                    comment=row["comment"],
                )
                self.ingest_row(cur_row)

    def sort_rows(self, reverse=True):
        if self.is_reverse != reverse:
            self.rows.sort(
                key=lambda row: (row.timestamp, row.z_index, row.tx_type, row.sent_currency, row.received_currency),
                reverse=reverse)
            self.is_reverse = reverse

    def _rows_export(self, format, reverse=True):
        self.sort_rows(reverse)
        rows = filter(lambda row: row.tx_type in et.TX_TYPES_CSVEXPORT, self.rows)

        if format in [et.FORMAT_KOINLY, et.FORMAT_COINPANDA, et.FORMAT_COINTELLI]:
            return rows

        # For non-koinly CSVs, convert LP_DEPOSIT/LP_WITHDRAW into transfers/omit/trades
        # (due to lack of native csv import support)
        out = []
        for row in rows:
            if row.tx_type == et.TX_TYPE_LP_DEPOSIT:
                if self.lp_treatment == et.LP_TREATMENT_OMIT:
                    continue
                elif self.lp_treatment == et.LP_TREATMENT_TRANSFERS:
                    out.append(self._row_as_transfer_out(row))
                elif self.lp_treatment == et.LP_TREATMENT_TRADES:
                    out.append(self._row_as_trade(row))
                else:
                    raise Exception("Bad condition in _rows_export().  lp_treatment=%s".format(self.lp_treatment))
            elif row.tx_type == et.TX_TYPE_LP_WITHDRAW:
                if self.lp_treatment == et.LP_TREATMENT_OMIT:
                    continue
                elif self.lp_treatment == et.LP_TREATMENT_TRANSFERS:
                    out.append(self._row_as_transfer_in(row))
                elif self.lp_treatment == et.LP_TREATMENT_TRADES:
                    out.append(self._row_as_trade(row))
                else:
                    raise Exception("Bad condition in _rows_export().  lp_treatment=%s".format(self.lp_treatment))
            else:
                out.append(row)

        return out

    def _row_as_transfer_out(self, row):
        return Row(
            timestamp=row.timestamp,
            tx_type=et.TX_TYPE_TRANSFER,
            received_amount="",
            received_currency="",
            sent_amount=row.sent_amount,
            sent_currency=row.sent_currency,
            fee=row.fee,
            fee_currency=row.fee_currency,
            exchange=row.exchange,
            wallet_address=row.wallet_address,
            txid=row.txid,
            url=row.url,
            z_index=row.z_index,
            comment=row.comment,
        )

    def _row_as_transfer_in(self, row):
        return Row(
            timestamp=row.timestamp,
            tx_type=et.TX_TYPE_TRANSFER,
            received_amount=row.received_amount,
            received_currency=row.received_currency,
            sent_amount="",
            sent_currency="",
            fee=row.fee,
            fee_currency=row.fee_currency,
            exchange=row.exchange,
            wallet_address=row.wallet_address,
            txid=row.txid,
            url=row.url,
            z_index=row.z_index,
            comment=row.comment,
        )

    def _row_as_trade(self, row):
        return Row(
            timestamp=row.timestamp,
            tx_type=et.TX_TYPE_TRADE,
            received_amount=row.received_amount,
            received_currency=row.received_currency,
            sent_amount=row.sent_amount,
            sent_currency=row.sent_currency,
            fee=row.fee,
            fee_currency=row.fee_currency,
            exchange=row.exchange,
            wallet_address=row.wallet_address,
            txid=row.txid,
            url=row.url,
            z_index=row.z_index,
            comment=row.comment,
        )

    def export_print(self):
        """ Prints transactions """
        print("Transactions:")
        print(self.export_string())

    def export_string(self):
        table = [et.ROW_FIELDS]
        table.extend([row.as_array() for row in self.rows])
        return tabulate(table)

    def export_for_test(self):
        table = [et.TEST_ROW_FIELDS]
        table.extend([row.as_array_short() for row in self.rows])

        return tabulate(table)

    def export_format(self, format, csvpath):
        if format == et.FORMAT_DEFAULT:
            self.export_default_csv(csvpath)
        elif format == et.FORMAT_BALANCES:
            self.export_balances_csv(csvpath)
        elif format == et.FORMAT_ACCOINTING:
            self.export_accointing_csv(csvpath)
            xlsxpath = csvpath.replace(".csv", ".xlsx")
            self.convert_csv_to_xlsx(csvpath, xlsxpath)
            return xlsxpath
        elif format == et.FORMAT_BITCOINTAX:
            self.export_bitcointax_csv(csvpath)
        elif format == et.FORMAT_BLOCKPIT:
            self.export_blockpit_csv(csvpath)
            xlsxpath = csvpath.replace(".csv", ".xlsx")
            self.convert_csv_to_xlsx(csvpath, xlsxpath)
            return xlsxpath
        elif format == et.FORMAT_COINLEDGER:
            self.export_coinledger_csv(csvpath)
        elif format == et.FORMAT_COINPANDA:
            self.export_coinpanda_csv(csvpath)
        elif format == et.FORMAT_COINTELLI:
            self.export_cointelli_csv(csvpath)
        elif format == et.FORMAT_COINTRACKING:
            self.export_cointracking_csv(csvpath)
        elif format == et.FORMAT_COINTRACKER:
            self.export_cointracker_csv(csvpath)
        elif format == et.FORMAT_CRYPTIO:
            self.export_cryptio_csv(csvpath)
        elif format == et.FORMAT_CRYPTOCOM:
            self.export_cryptocom_csv(csvpath)
        elif format == et.FORMAT_CRYPTOTAXCALCULATOR:
            self.export_calculator_csv(csvpath)
        elif format == et.FORMAT_CRYPTOWORTH:
            self.export_cryptoworth_csv(csvpath)
        elif format == et.FORMAT_KOINLY:
            self.export_koinly_csv(csvpath)
        elif format == et.FORMAT_RECAP:
            self.export_recap_csv(csvpath)
        elif format == et.FORMAT_TAXBIT:
            self.export_taxbit_csv(csvpath)
        elif format == et.FORMAT_TOKENTAX:
            self.export_tokentax_csv(csvpath)
        elif format == et.FORMAT_ZENLEDGER:
            self.export_zenledger_csv(csvpath)

        return csvpath

    def export_default_csv(self, csvpath=None, truncate=0):
        self.sort_rows(reverse=True)

        rows = self.rows
        table = [et.ROW_FIELDS]
        if truncate:
            table.extend([row.as_array() for row in rows[0:truncate]])
        else:
            table.extend([row.as_array() for row in rows])

        if csvpath:
            with open(csvpath, 'w', newline='', encoding='utf-8') as f:
                mywriter = csv.writer(f)
                mywriter.writerows(table)
                logging.info("Wrote to %s", csvpath)
            return None
        else:
            # Return as string
            output = io.StringIO()
            writer = csv.writer(output, lineterminator="\n")
            writer.writerows(table)
            return output.getvalue()

    def export_cryptoworth_csv(self, csvpath):
        self.export_default_csv(csvpath)

    def export_cointracking_csv(self, csvpath):
        """ Write CSV, suitable for import into cointracking.info """
        cointracking_types = {
            et.TX_TYPE_AIRDROP: "Airdrop",
            et.TX_TYPE_STAKING: "Staking",
            et.TX_TYPE_TRADE: "Trade",
            et.TX_TYPE_TRANSFER: et.TX_TYPE_TRANSFER,
            et.TX_TYPE_INCOME: "Income",
            et.TX_TYPE_SPEND: "Spend",
            et.TX_TYPE_BORROW: et.TX_TYPE_TRANSFER,
            et.TX_TYPE_REPAY: et.TX_TYPE_TRANSFER,
        }
        rows = self._rows_export(et.FORMAT_COINTRACKING)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.CT_FIELDS)

            # data rows
            for row in rows:
                # Determine type
                ct_type = cointracking_types[row.tx_type]
                if ct_type == et.TX_TYPE_TRANSFER:
                    if row.received_amount and not row.sent_amount:
                        ct_type = "Deposit"
                    elif row.sent_amount and not row.received_amount:
                        ct_type = "Withdrawal"
                    else:
                        ct_type = "Deposit"
                        logging.error("Bad condition in export_cointracking_csv(): {}, {}, {}".format(
                            row.received_amount, row.sent_amount, row.as_array()))

                # id that determines duplicates
                txid_cointracking = str(row.txid) + "." + str(row.received_currency) + "." + str(row.sent_currency)

                # add txid to comment, as helpful info in cointracking UI
                if row.comment:
                    comment = "{} {}".format(row.comment, row.txid)
                else:
                    comment = row.txid

                # Adjust amount(s) for fee according to cointracking spec
                # https://cointracking.freshdesk.com/en/support/solutions/articles/29000007202-entering-fees
                adj_sent_amount, adj_received_amount, other_fee_line = self._cointracking_fee_adjustments(ct_type, row, comment)

                line = [
                    ct_type,                                             # "Staking" | "Airdrop" | "Trade
                    adj_received_amount,                                 # Buy Amount
                    self._cointracking_code(row.received_currency),      # Buy Currency
                    adj_sent_amount,                                     # Sell Amount
                    self._cointracking_code(row.sent_currency),          # Sell Currency
                    row.fee,                                             # Fee
                    self._cointracking_code(row.fee_currency),           # Fee Currency
                    row.exchange,                                        # Exchange
                    row.wallet_address,                                  # Trade-Group
                    comment,                                             # Comment
                    row.timestamp,                                       # Date
                    txid_cointracking                                    # Tx-ID
                ]
                mywriter.writerow(line)

                if other_fee_line:
                    mywriter.writerow(other_fee_line)

        logging.info("Wrote to %s", csvpath)

    def _cointracking_fee_adjustments(self, ct_type, row, comment):
        if not row.fee:
            return row.sent_amount, row.received_amount, None
        elif "multicurrency fee" in comment:
            return row.sent_amount, row.received_amount, None
        elif ct_type == "Deposit" and row.tx_type != et.TX_TYPE_BORROW:
            return row.sent_amount, row.received_amount, None
        elif row.received_amount and row.received_currency == row.fee_currency:
            # adjust received amount
            return row.sent_amount, float(row.received_amount) - float(row.fee), None
        elif row.sent_amount and row.sent_currency == row.fee_currency:
            # adjust sent amount
            return float(row.sent_amount) + float(row.fee), row.received_amount, None
        elif row.fee and row.fee_currency not in (row.received_currency, row.sent_currency):
            # other currency fee case: add csv "Other Fee" row
            txid_other_fee = str(row.txid) + ".fee"
            other_fee_line = [
                "Other Fee",
                "",                                            # Buy Amount
                "",                                            # Buy Currency
                row.fee,                                       # Sell Amount
                self._cointracking_code(row.fee_currency),     # Sell Currency
                "",                                            # Fee
                "",                                            # Fee Currency
                row.exchange,                                  # Exchange
                row.wallet_address,                            # Trade-Group
                "fee for {}".format(row.txid),                 # Comment
                row.timestamp,                                 # Date
                txid_other_fee                                 # Tx-ID
            ]
            return row.sent_amount, row.received_amount, other_fee_line
        else:
            logging.critical("Bad condition in _cointracking_fee_adjustments(): unable to handle txid=%s", row.txid)
            return row.sent_amount, row.received_amount, None

    def export_tokentax_csv(self, csvpath):
        """ Write CSV, suitable for import into TokenTax """
        tokentax_types = {
            et.TX_TYPE_AIRDROP: "Airdrop",
            et.TX_TYPE_STAKING: "Staking",
            et.TX_TYPE_TRADE: "Trade",
            et.TX_TYPE_TRANSFER: "Transfer",
            et.TX_TYPE_INCOME: "Income",
            et.TX_TYPE_SPEND: "Spend",
            et.TX_TYPE_BORROW: "Transfer",
            et.TX_TYPE_REPAY: "Transfer",
        }
        rows = self._rows_export(et.FORMAT_TOKENTAX)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.TT_FIELDS)

            # data rows
            for row in rows:
                # Determine tx_type
                tx_type = tokentax_types[row.tx_type]
                if tx_type == "Transfer":
                    if row.received_amount and not row.sent_amount:
                        tx_type = "Deposit"
                    elif row.sent_amount and not row.received_amount:
                        tx_type = "Withdrawal"
                    else:
                        tx_type = "Deposit"
                        logging.error("Bad condition in export_tokentax_csv(): {}, {}, {}".format(
                            row.received_amount, row.sent_amount, row.as_array()))

                if row.comment:
                    comment = "{} {}".format(row.comment, row.txid)
                else:
                    comment = row.txid

                line = [
                    tx_type,                                             # "Staking" | "Airdrop" | "Trade
                    row.received_amount,                                 # BuyAmount
                    row.received_currency,                               # BuyCurrency
                    row.sent_amount,                                     # SellAmount
                    row.sent_currency,                                   # SellCurrency
                    row.fee,                                             # FeeAmount
                    row.fee_currency,                                    # FeeCurrency
                    row.exchange,                                        # Exchange
                    row.wallet_address,                                  # Group
                    comment,                                             # Comment
                    self._tokentax_timestamp(row.timestamp)              # Date
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def export_cointracker_csv(self, csvpath):
        """ Write CSV, suitable for import into Cointracker """
        tags = {
            et.TX_TYPE_AIRDROP: "airdrop",
            et.TX_TYPE_STAKING: "staked",
            et.TX_TYPE_TRADE: "",
            et.TX_TYPE_TRANSFER: "",
            et.TX_TYPE_INCOME: "payment",
            et.TX_TYPE_SPEND: "",
            et.TX_TYPE_BORROW: "",
            et.TX_TYPE_REPAY: "",
        }
        rows = self._rows_export(et.FORMAT_COINTRACKER)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.CR_FIELDS)

            # data rows
            for row in rows:
                tag = tags[row.tx_type]

                line = [
                    self._cointracker_timestamp(row.timestamp),          # Date
                    row.received_amount,                                 # Received Quantity
                    self._cointracker_code(row.received_currency),       # Received Currency
                    row.sent_amount,                                     # Sent Quantity
                    self._cointracker_code(row.sent_currency),           # Sent Currency
                    row.fee,                                             # Fee Amount
                    self._cointracker_code(row.fee_currency),            # Fee Currency
                    tag,                                                 # Tag
                    row.txid                                             # extra field added for user danb
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def export_coinledger_csv(self, csvpath):
        """ Write CSV, suitable for import into CoinLedger (cryptotrader.tax) """
        tags = {
            et.TX_TYPE_AIRDROP: "Airdrop",
            et.TX_TYPE_STAKING: "Staking",
            et.TX_TYPE_TRADE: "",
            et.TX_TYPE_TRANSFER: "Transfer",
            et.TX_TYPE_INCOME: "Income",
            et.TX_TYPE_SPEND: "Gift Sent",
            et.TX_TYPE_BORROW: "Transfer",
            et.TX_TYPE_REPAY: "Transfer",
        }
        rows = self._rows_export(et.FORMAT_COINLEDGER)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.CL_FIELDS)

            # data rows
            for row in rows:
                tag = tags[row.tx_type]
                if tag == "Transfer":
                    if row.received_amount and not row.sent_amount:
                        tag = "Deposit"
                    if row.sent_amount and not row.received_amount:
                        tag = "Withdrawal"

                line = [
                    self._coinledger_timestamp(row.timestamp),           # Date (UTC)
                    "{}_blockchain".format(self.ticker.lower()),         # Platform (Optional)
                    self._coinledger_code(row.sent_currency),            # Asset Sent
                    row.sent_amount,                                     # Amount Sent
                    self._coinledger_code(row.received_currency),        # Asset Received
                    row.received_amount,                                 # Amount Received
                    self._coinledger_code(row.fee_currency),             # Fee Currency (Optional)"
                    row.fee,                                             # Fee Amount (Optional)"
                    tag,                                                 # Type
                    row.comment,                                         # Description (Optional)
                    row.txid                                             # TxHash (Optional)
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def _coinledger_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "08/14/2021 15:25:43"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%m/%d/%Y %H:%M:%S")

    def _coinledger_code(self, currency):
        return currency

    def export_cryptocom_csv(self, csvpath):
        """ Write CSV, suitable for import into tax.crypto.com """
        tags = {
            et.TX_TYPE_AIRDROP: "airdrop",
            et.TX_TYPE_STAKING: "reward",
            et.TX_TYPE_TRADE: "swap",
            et.TX_TYPE_TRANSFER: "transfer",
            et.TX_TYPE_INCOME: "payment",
            et.TX_TYPE_SPEND: "payment",
            et.TX_TYPE_BORROW: "transfer",
            et.TX_TYPE_REPAY: "transfer",
        }
        rows = self._rows_export(et.FORMAT_CRYPTOCOM)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.CRCOM_FIELDS)

            # data rows
            for row in rows:
                # determine Type field
                row_type = tags[row.tx_type]

                # determine Received Currency, Received Amount, Sent Currency, Sent Amount
                if row_type == "transfer":
                    # cryptocom has strange spec where receive/sent should be same on transfers between users' wallets
                    if row.received_amount:
                        amt, cur = row.received_amount, row.received_currency
                    elif row.sent_amount:
                        amt, cur = row.sent_amount, row.sent_currency
                    else:
                        logging.error("export_crytocom_csv(): bad condition row=%s", row.as_array())
                    received_amount, received_currency = amt, cur
                    sent_amount, sent_currency = amt, cur
                else:
                    received_amount = row.received_amount
                    received_currency = row.received_currency
                    sent_currency = row.sent_currency
                    sent_amount = row.sent_amount

                # Determine fee and fee currency
                if row.tx_type in [et.TX_TYPE_AIRDROP, et.TX_TYPE_STAKING]:
                    # To workaround "Fee is not allowed for received types" error.
                    # This is probably incorrect implementation by tax.crypto.com, but
                    # failed import is worse result for user.
                    fee = ""
                    fee_currency = ""
                else:
                    fee = row.fee
                    fee_currency = row.fee_currency

                line = [
                    self._cryptocom_timestamp(row.timestamp),  # Date
                    row_type,                                  # Type
                    received_currency,                         # Received Currency
                    received_amount,                           # Received Amount
                    "",                                        # Received Net Worth
                    sent_currency,                             # Sent Currency
                    sent_amount,                               # Sent Amount
                    "",                                        # Sent Net Worth
                    fee_currency,                              # Fee Currency
                    fee,                                       # Fee Amount
                    ""                                         # Fee Net Worth
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def _cryptocom_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "08/14/2021 15:25:43"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%m/%d/%Y %H:%M:%S")

    def export_koinly_csv(self, csvpath):
        """ Write CSV, suitable for import into Koinly """
        self.koinly_nullmap.load()
        rows = self._rows_export(et.FORMAT_KOINLY, reverse=False)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.KOINLY_FIELDS)

            # data rows
            for row in rows:
                if row.tx_type == et.TX_TYPE_TRADE:
                    label = ""
                elif row.tx_type == et.TX_TYPE_AIRDROP:
                    label = "airdrop"
                elif row.tx_type == et.TX_TYPE_STAKING:
                    label = "staking"
                elif row.tx_type == et.TX_TYPE_INCOME:
                    label = "other income"
                elif row.tx_type == et.TX_TYPE_SPEND:
                    label = "cost"
                elif row.tx_type == et.TX_TYPE_BORROW:
                    label = ""
                elif row.tx_type == et.TX_TYPE_REPAY:
                    label = ""
                elif row.tx_type == et.TX_TYPE_TRANSFER:
                    label = ""
                elif row.tx_type == et.TX_TYPE_LP_DEPOSIT:
                    label = "Liquidity In"
                elif row.tx_type == et.TX_TYPE_LP_WITHDRAW:
                    label = "Liquidity Out"
                else:
                    logging.error("koinly: unable to handle tx_type=%s", row.tx_type)

                # Currency fields
                sent_currency = self.koinly_currency(row.sent_currency)
                received_currency = self.koinly_currency(row.received_currency)
                fee_currency = self.koinly_currency(row.fee_currency)

                # Description field
                # Add note to description if LP token symbol mapped to NULL*
                description = row.comment
                if sent_currency.startswith("NULL"):
                    description += " " + row.sent_currency
                if received_currency.startswith("NULL"):
                    description += " " + row.received_currency
                if fee_currency.startswith("NULL"):
                    description += " " + row.fee_currency

                line = [
                    row.timestamp,                                       # Date
                    row.sent_amount,                                     # Sent Amount
                    sent_currency,                                       # Sent Currency
                    row.received_amount,                                 # Received Amount
                    received_currency,                                   # Received Currency
                    row.fee,                                             # Fee Amount
                    fee_currency,                                        # Fee Currency
                    "",                                                  # Net Worth Amount
                    "",                                                  # Net Worth Currency
                    label,                                               # Label
                    description,                                         # Description
                    row.txid                                             # TxHash
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)
        self.koinly_nullmap.flush()

    def koinly_currency(self, currency):
        # Reference: https://app.koinly.io/p/markets?search=STARS
        remap = {
            TICKER_LUNA1: {
                "APOLLO": "ID:28478",
                "ASTRO": "ID:48993",
                "BETH": "ID:30493",
                "LOOP": "ID:10933",
                "LUNI": "ID:26855",
                "MINE": "ID:21256",
                "PSI": "ID:106376",
            },
            TICKER_ATOM: {
                "STARS": "ID:36899",
            },
            TICKER_ALGO: {
                "AKITA": "ID:132343",
                "AKTA": "ID:182292",
                "DEGEN": "ID:124845",
                "DEFLY": "ID:171818",
                "OCTO": "ID:174045",
                "GALGO": "ID:5217593"
            },
            TICKER_LUNA2: {
                "LUNA": "ID:6089",
            }
        }

        if self._is_koinly_lp(currency):
            return self.koinly_nullmap.get_null_symbol(currency)
        if currency and currency.upper() in remap.get(self.ticker, {}):
            return remap[self.ticker][currency.upper()]
        return currency

    def _is_koinly_lp(self, currency):
        """ Returns True if lp currency should be replaced with NULL* in koinly CSV (i.e. GAMM-22, LP_MIR_UST) """
        if currency.startswith("LP_"):
            return True
        if currency.startswith("GAMM-"):
            return True
        return False

    def export_calculator_csv(self, csvpath):
        """ Write CSV, suitable for import into cryptataxcalculator.io """
        rows = self._rows_export(et.FORMAT_CRYPTOTAXCALCULATOR)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.CALC_FIELDS)

            # data rows
            for row in rows:
                # Determine type field
                if row.tx_type == et.TX_TYPE_STAKING:
                    type = "interest"
                elif row.tx_type == et.TX_TYPE_AIRDROP:
                    type = "airdrop"
                elif row.tx_type == et.TX_TYPE_TRADE:
                    type = "sell"
                elif row.tx_type == et.TX_TYPE_TRANSFER:
                    if row.received_amount:
                        type = "transfer-in"
                    elif row.sent_amount:
                        type = "transfer-out"
                elif row.tx_type == et.TX_TYPE_INCOME:
                    type = "income"
                elif row.tx_type == et.TX_TYPE_SPEND:
                    type = "sell"
                elif row.tx_type == et.TX_TYPE_BORROW:
                    type = "borrow"
                elif row.tx_type == et.TX_TYPE_REPAY:
                    type = "loan-repayment"
                else:
                    type = ""
                    logging.critical("No type determined for tx_type=%s", row.tx_type)

                # Determine base_currency, base_amount, quote_currency, quote_amount
                if row.received_amount and row.sent_amount:
                    base_currency = row.sent_currency
                    base_amount = row.sent_amount
                    quote_currency = row.received_currency
                    quote_amount = row.received_amount
                elif row.received_amount:
                    base_currency = row.received_currency
                    base_amount = row.received_amount
                    quote_currency = ""
                    quote_amount = ""
                elif row.sent_amount:
                    base_currency = row.sent_currency
                    base_amount = row.sent_amount
                    quote_currency = ""
                    quote_amount = ""
                else:
                    logging.error("Bad condition.  No received amount and no sent amount.")
                    base_currency = ""
                    base_amount = ""
                    quote_currency = ""
                    quote_amount = ""

                line = [
                    self._calculator_timestamp(row.timestamp),  # Timestamp
                    type,                                       # Type
                    base_currency,                              # Base Currency
                    base_amount,                                # Base Amount
                    quote_currency,                             # Quote Currency
                    quote_amount,                               # Quote Amount
                    row.fee_currency,                           # Fee Currency
                    row.fee,                                    # Fee Amount
                    "",                                         # From
                    "",                                         # To
                    row.txid,                                   # ID
                    row.comment                                 # Description
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def _calculator_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "08/14/2021 15:25:43"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

        return dt.strftime("%d/%m/%Y %H:%M:%S")

    def export_accointing_csv(self, csvpath):
        """ Writes CSV, whose xlsx translation is suitable for import into Accointing """
        rows = self._rows_export(et.FORMAT_ACCOINTING)
        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.ACCOINT_FIELDS)

            # data rows
            for row in rows:
                # Determine transaction_type, classification
                if row.tx_type == et.TX_TYPE_STAKING:
                    transaction_type = "deposit"
                    classification = "staked"
                elif row.tx_type == et.TX_TYPE_AIRDROP:
                    transaction_type = "deposit"
                    classification = "airdrop"
                elif row.tx_type == et.TX_TYPE_TRADE:
                    transaction_type = "order"
                    classification = ""
                elif row.tx_type == et.TX_TYPE_SPEND:
                    transaction_type = "withdraw"
                    classification = "payment"
                elif row.tx_type == et.TX_TYPE_TRANSFER:
                    if row.sent_amount:
                        transaction_type = "withdraw"
                    elif row.received_amount:
                        transaction_type = "deposit"
                    else:
                        transaction_type = ""
                        logging.error("Bad condition for transfer")
                    classification = ""
                elif row.tx_type == et.TX_TYPE_INCOME:
                    transaction_type = "deposit"
                    classification = "income"
                elif row.tx_type == et.TX_TYPE_BORROW:
                    transaction_type = "deposit"
                    classification = ""
                elif row.tx_type == et.TX_TYPE_REPAY:
                    transaction_type = "withdraw"
                    classification = ""
                else:
                    transaction_type = ""
                    classification = ""
                    logging.critical("Transaction not handled correctly.  Fix this!")

                line = [
                    transaction_type,                            # transactionType
                    self._accointing_timestamp(row.timestamp),   # date
                    row.received_amount,                         # inBuyAmount
                    row.received_currency,                       # inBuyAsset
                    row.sent_amount,                             # outSellAmount
                    row.sent_currency,                           # outSellAsset
                    row.fee,                                     # feeAmount
                    row.fee_currency,                            # feeAsset
                    classification,                              # classification
                    row.txid,                                    # operationId
                    row.comment,                                 # comments
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def convert_csv_to_xlsx(self, csvpath, xlsxpath):
        read_file = pd.read_csv(csvpath)
        read_file.to_excel(xlsxpath, index=None, header=True)
        logging.info("Wrote to %s", xlsxpath)

    def export_zenledger_csv(self, csvpath):
        """ Writes CSV, suitable for import into ZenLedger """
        zen_tx_types = {
            et.TX_TYPE_AIRDROP: "airdrop",
            et.TX_TYPE_STAKING: "staking",
            et.TX_TYPE_TRADE: "Trade",
            et.TX_TYPE_TRANSFER: "transfer",
            et.TX_TYPE_INCOME: "misc reward",
            et.TX_TYPE_SPEND: "payment",
            et.TX_TYPE_BORROW: "transfer",
            et.TX_TYPE_REPAY: "transfer"
        }
        rows = self._rows_export(et.FORMAT_ZENLEDGER)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.ZEN_FIELDS)

            # data rows
            for row in rows:
                # Determine type
                cur_type = zen_tx_types[row.tx_type]
                if cur_type == "transfer":
                    if row.received_amount and not row.sent_amount:
                        cur_type = "Receive"
                    elif row.sent_amount and not row.received_amount:
                        cur_type = "Send"
                    else:
                        cur_type = "Receive"
                        logging.error("Bad condition in exporter_zenledger_csv: {}, {}, {}".format(
                            row.received_amount, row.sent_amount, row.as_array()
                        ))

                line = [
                    row.timestamp,          # Timestamp
                    cur_type,                # Type
                    row.received_amount,    # IN Amount
                    row.received_currency,  # IN Currency
                    row.sent_amount,        # OUT Amount
                    row.sent_currency,      # OUT Currency
                    row.fee,                # Fee Amount
                    row.fee_currency,       # Fee Currency
                    row.exchange,           # Exchange
                    ""                      # US Based
                ]
                mywriter.writerow(line)
        logging.info("Wrote to %s", csvpath)

    def export_bitcointax_csv(self, csvpath):
        """ Writes CSV, suitable for import into bitcoin.tax """
        actions = {
            et.TX_TYPE_AIRDROP: "INCOME",
            et.TX_TYPE_STAKING: "INCOME",
            et.TX_TYPE_TRADE: "BUY",
            et.TX_TYPE_TRANSFER: None,
            et.TX_TYPE_INCOME: "INCOME",
            et.TX_TYPE_SPEND: "SPEND",
            et.TX_TYPE_BORROW: None,
            et.TX_TYPE_REPAY: None,
        }
        rows = self._rows_export(et.FORMAT_BITCOINTAX)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.BTAX_FIELDS)

            # data rows
            for row in rows:
                action = actions[row.tx_type]
                if action is None:
                    continue

                if action == "INCOME":
                    symbol = row.received_currency
                    volume = row.received_amount
                    currency = ""
                    total = ""
                elif action == "SPEND":
                    symbol = row.sent_currency
                    volume = row.sent_amount
                    currency = ""
                    total = ""
                elif action == "BUY":
                    symbol = row.received_currency
                    volume = row.received_amount
                    currency = row.sent_currency
                    total = row.sent_amount
                else:
                    raise Exception("export_bitcointax_csv(): Bad condition for action={}".format(action))

                line = [
                    self._bitcointax_timestamp(row.timestamp),  # Date
                    action,                                     # Action
                    symbol,                                     # Symbol
                    volume,                                     # Volume
                    currency,                                   # Currency
                    total,                                      # Total
                    row.fee,                                    # Fee
                    row.fee_currency,                           # FeeCurrency
                    row.txid,                                   # Memo
                ]
                mywriter.writerow(line)
        logging.info("Wrote to %s", csvpath)

    def export_recap_csv(self, csvpath):
        """ Write CSV, suitable for import into Recap """
        self.sort_rows(reverse=True)
        rows = self._rows_export(et.FORMAT_RECAP)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.RECAP_FIELDS)

            # data rows
            for row in rows:
                # Determine type field
                if row.tx_type == et.TX_TYPE_STAKING:
                    cur_type = "StakingReward"
                elif row.tx_type == et.TX_TYPE_AIRDROP:
                    cur_type = "Airdrop"
                elif row.tx_type == et.TX_TYPE_TRADE:
                    cur_type = "Trade"
                elif row.tx_type == et.TX_TYPE_TRANSFER:
                    if row.received_amount:
                        cur_type = "Deposit"
                    elif row.sent_amount:
                        cur_type = "Withdrawal"
                elif row.tx_type == et.TX_TYPE_INCOME:
                    cur_type = "Income"
                elif row.tx_type == et.TX_TYPE_SPEND:
                    cur_type = "Purchase"
                elif row.tx_type == et.TX_TYPE_BORROW:
                    cur_type = "Deposit"
                elif row.tx_type == et.TX_TYPE_REPAY:
                    cur_type = "Withdrawal"
                else:
                    cur_type = ""
                    logging.critical("No type determined for tx_type=%s", row.tx_type)

                line = [
                    cur_type,                                   # Type
                    row.timestamp,                              # Date
                    row.received_amount,                        # InOrBuyAmount
                    row.received_currency,                      # InOrBuyCurrency
                    row.sent_amount,                            # OutOrSellAmount
                    row.sent_currency,                          # OutOrSellCurrency
                    row.fee,                                    # FeeAmount
                    row.fee_currency,                           # FeeCurrency
                    row.comment,                                # Description
                    row.txid,                                   # ID
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def export_coinpanda_csv(self, csvpath):
        """ Writes CSV, suitable for import into bitcoin.tax """
        labels = {
            et.TX_TYPE_AIRDROP: "Airdrop",
            et.TX_TYPE_STAKING: "Staking",
            et.TX_TYPE_TRADE: "Swap",
            et.TX_TYPE_TRANSFER: "",
            et.TX_TYPE_INCOME: "Income",
            et.TX_TYPE_SPEND: "Cost",
            et.TX_TYPE_BORROW: "Receive Loan",
            et.TX_TYPE_REPAY: "Repay Loan",
            et.TX_TYPE_LP_DEPOSIT: "Liquidity in",
            et.TX_TYPE_LP_WITHDRAW: "Liquidity out",
        }

        rows = self._rows_export(et.FORMAT_COINPANDA)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.CP_FIELDS)

            # data rows
            for row in rows:
                # Determine Type
                if row.sent_amount and row.received_amount:
                    row_type = "Trade"
                elif row.sent_amount:
                    row_type = "Send"
                elif row.received_amount:
                    row_type = "Receive"
                else:
                    logging.critical("exporter_coinpanda_csv(): bad condition for row type %s", row.as_array())
                    row_type = ""

                # Determine Label
                label = labels[row.tx_type]
                if "nft" in row.comment:
                    label = "NFT"

                line = [
                    row.timestamp,          # Date
                    row_type,               # Type
                    row.sent_amount,        # Sent Amount
                    row.sent_currency,      # Sent Currency
                    row.received_amount,    # Received Amount
                    row.received_currency,  # Received Currency
                    row.fee,                # Fee Amount
                    row.fee_currency,       # Fee Currency
                    label,                  # Label
                    row.comment,            # Description
                    row.txid,               # TxHash
                ]
                mywriter.writerow(line)
        logging.info("Wrote to %s", csvpath)

    def export_taxbit_csv(self, csvpath):
        TAXBIT_TYPES = {
            et.TX_TYPE_STAKING: "Income",
            et.TX_TYPE_AIRDROP: "Income",
            et.TX_TYPE_TRADE: "Trade",
            et.TX_TYPE_SPEND: "Expense",
            et.TX_TYPE_INCOME: "Income",
            et.TX_TYPE_TRANSFER: "Transfer Unknown",
            et.TX_TYPE_BORROW: "Transfer Unknown",
            et.TX_TYPE_REPAY: "Transfer Unknown"
        }
        rows = self._rows_export(et.FORMAT_TAXBIT)
        if not self.ticker:
            logging.error("Unable to identify tx_source.  Missing ticker")
        tx_source = "{} WALLET".format(self.ticker.upper())

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.TAXBIT_FIELDS)

            # data rows
            for row in rows:
                # Determine Transaction Type
                tb_type = TAXBIT_TYPES[row.tx_type]
                if tb_type in ["Transfer Unknown"]:
                    if row.received_amount:
                        tb_type = "Transfer In"
                    else:
                        tb_type = "Transfer Out"

                # Determine Sending Source and Receiving Destination
                if tb_type == "Income":
                    sending_source = ""
                    receiving_destination = tx_source
                elif tb_type == "Trade":
                    sending_source = tx_source
                    receiving_destination = tx_source
                elif tb_type == "Expense":
                    sending_source = tx_source
                    receiving_destination = ""
                elif tb_type == "Income":
                    sending_source = ""
                    receiving_destination = tx_source
                elif tb_type == "Transfer In":
                    sending_source = ""
                    receiving_destination = tx_source
                elif tb_type == "Transfer Out":
                    sending_source = tx_source
                    receiving_destination = ""
                else:
                    raise Exception("Bad condition: unable to determined tb_type for txid {}".format(row.txid))

                # Create an ID that determines duplicates
                exchange_transaction_id = "{}.{}.{}".format(row.txid, row.sent_currency, row.received_currency)

                line = [
                    self._taxbit_timestamp(row.timestamp),       # Date and Time
                    tb_type,                                     # Transaction Type
                    row.sent_amount,                             # Sent Quantity
                    row.sent_currency,                           # Sent Currency
                    sending_source,                              # Sending Source
                    row.received_amount,                         # Received Quantity
                    row.received_currency,                       # Received Currency
                    receiving_destination,                       # Receiving Destination
                    row.fee,                                     # Fee
                    row.fee_currency,                            # Fee Currency
                    exchange_transaction_id,                     # Exchange Transaction ID (determines duplicates)
                    row.txid                                     # Blockchain Transaction Hash
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def export_cointelli_csv(self, csvpath):
        rows = self._rows_export(et.FORMAT_COINTELLI)
        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.COINTELLI_FIELDS)

            # data rows
            for row in rows:
                # Determine transaction_type, classification
                if row.tx_type == et.TX_TYPE_STAKING:
                    transaction_type = "Staking Reward"
                elif row.tx_type == et.TX_TYPE_AIRDROP:
                    transaction_type = "Airdrop"
                elif row.tx_type == et.TX_TYPE_TRADE:
                    transaction_type = "Trade"
                elif row.tx_type == et.TX_TYPE_SPEND:
                    transaction_type = "Payment Sent"
                elif row.tx_type == et.TX_TYPE_TRANSFER:
                    if row.sent_amount:
                        transaction_type = "Uncategorized Outgoing"
                    elif row.received_amount:
                        transaction_type = "Uncategorized Incoming"
                    else:
                        transaction_type = ""
                        logging.error("Bad condition for transfer")
                elif row.tx_type == et.TX_TYPE_INCOME:
                    transaction_type = "Income"
                elif row.tx_type == et.TX_TYPE_BORROW:
                    transaction_type = "Borrowing"
                elif row.tx_type == et.TX_TYPE_REPAY:
                    transaction_type = "Repayment"
                elif row.tx_type == et.TX_TYPE_LP_DEPOSIT:
                    transaction_type = "Trade"
                elif row.tx_type == et.TX_TYPE_LP_WITHDRAW:
                    transaction_type = "Trade"
                else:
                    transaction_type = ""
                    logging.critical("Transaction not handled correctly.  Fix this!")

                comment = row.comment + " " + row.txid

                line = [
                    self._cointelli_timestamp(row.timestamp),   # Timestamp
                    transaction_type,                           # Type
                    row.sent_currency,                          # Out Currency
                    row.sent_amount,                            # Out Quantity
                    row.received_currency,                      # In Currency
                    row.received_amount,                        # In Quantity
                    row.fee_currency,                           # Fee Currency
                    row.fee,                                    # Fee Quantity
                    comment,                                    # Comments
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def export_blockpit_csv(self, csvpath):
        """ Experimental-state CSV for blockpit.io """
        BLOCKPIT_TYPES = {
            et.TX_TYPE_STAKING: "staking",
            et.TX_TYPE_AIRDROP: "airdrop",
            et.TX_TYPE_TRADE: "trade",
            et.TX_TYPE_SPEND: "expense",
            et.TX_TYPE_INCOME: "staking",
            et.TX_TYPE_TRANSFER: "transfer",
            et.TX_TYPE_BORROW: "transfer",
            et.TX_TYPE_REPAY: "transfer"
        }
        rows = self._rows_export(et.FORMAT_BLOCKPIT)

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.BLOCKPIT_FIELDS)

            # data rows
            for i, row in enumerate(rows):
                # Determine Transaction Type
                bl_type = BLOCKPIT_TYPES[row.tx_type]
                if bl_type == "transfer":
                    if row.sent_amount:
                        bl_type = "withdrawal"
                    else:
                        bl_type = "deposit"

                exchange_name = self.ticker + "_blockchain"
                depot_name = "staketax_" + self.wallet_address

                line = [
                    self._blockpit_id(row),                   # id
                    exchange_name,                            # exchange_name
                    depot_name,                               # depot_name
                    self._blockpit_timestamp(row.timestamp),  # transaction_date
                    row.received_currency,                    # buy_asset
                    row.received_amount,                      # buy_amount
                    row.sent_currency,                        # sell_asset
                    row.sent_amount,                          # sell_amount
                    row.fee_currency,                         # fee_asset
                    row.fee,                                  # fee_amount
                    bl_type,                                  # transaction_type
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def _blockpit_id(self, row):
        # Convert "2021-08-04 15:25:43" to "14.08.2021 15:25:43"
        dt = datetime.strptime(row.timestamp, "%Y-%m-%d %H:%M:%S")

        id = str(int(time.mktime(dt.timetuple())))
        return id

    def _blockpit_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "14.08.2021 15:25:43"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

        return dt.strftime("%d.%m.%Y %H:%M:%S")

    def export_cryptio_csv(self, csvpath):
        # row.tx_type -> (orderType, internalTransfer)
        TRANSFER_TEMP_TYPE = "TRANSFER_TEMP_TYPE"
        cryptio_types = {
            et.TX_TYPE_AIRDROP: ("deposit", 0),
            et.TX_TYPE_STAKING: ("deposit", 0),
            et.TX_TYPE_TRADE: ("trade", 0),
            et.TX_TYPE_TRANSFER: (TRANSFER_TEMP_TYPE, 1),
            et.TX_TYPE_INCOME: ("deposit", 0),
            et.TX_TYPE_SPEND: ("withdraw", 0),
            et.TX_TYPE_BORROW: (TRANSFER_TEMP_TYPE, 1),
            et.TX_TYPE_REPAY: (TRANSFER_TEMP_TYPE, 1),
        }

        rows = self._rows_export(et.FORMAT_CRYPTIO)
        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.CRYPTIO_FIELDS)

            # data rows
            for row in rows:

                # Determine orderType and internalTransfer
                order_type, internal_transfer = cryptio_types[row.tx_type]
                if order_type == TRANSFER_TEMP_TYPE:
                    if row.sent_amount:
                        order_type = "withdraw"
                    elif row.received_amount:
                        order_type = "deposit"
                    else:
                        raise Exception("export_cryptio_csv(): Unable to handle transfer case with no amounts")

                line = [
                    row.timestamp,          # transactionDate
                    order_type,             # orderType
                    row.txid,               # txhash
                    row.received_currency,  # incomingAsset
                    row.received_amount,    # incomingVolume
                    row.sent_currency,      # outgoingAsset
                    row.sent_amount,        # outgoingVolume
                    row.fee_currency,       # feeAsset
                    row.fee,                # feeVolume
                    "",                     # otherParties
                    row.comment,            # note
                    1,                      # success
                    internal_transfer,      # internalTransfer
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def _bitcointax_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "2021-08-04 15:25:43 -0000"
        return ts + " -0000"

    def _taxbit_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "2021-08-04T15:25:43Z"
        d, t = ts.split(" ")
        return "{}T{}Z".format(d, t)

    def _accointing_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "08/14/2021 15:25:43"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

        return dt.strftime("%m/%d/%Y %H:%M:%S")

    def _tokentax_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "08/14/2021 15:25:43"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

        return dt.strftime("%m/%d/%Y %H:%M:%S")

    def _cointelli_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "08/14/2021 15:25:43"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

        return dt.strftime("%m/%d/%Y %H:%M:%S")

    def _utc_to_local(self, date_string, timezone_string):
        dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        utc_dt = pytz.utc.localize(dt)
        local_tz = timezone(timezone_string)
        local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))

        return local_dt.strftime("%Y-%m-%d %H:%M:%S")

    def _cointracking_code(self, currency):
        # Reference: https://cointracking.info/coin_charts.php
        remap = {
            "ANC": "ANC2",
            "ASTRO": "ASTRO5",
            "ATOM": "ATOM2",
            "GLOW": "GLOW3",
            "BETH": "BETH3",
            "LOOP": "LOOP2",
            "LUNI": "LUNI2",
            "MARS": "MARS6",
            "MINE": "MINE2",
            "MIR": "MIR2",
            "ORION": "ORION2",
            "PLY": "PLY3",
            "PRISM": "PRISM3",
            "PSI": "PSI2",
            "SD": "SD2",
            "SOL": "SOL2",
            "STARS": "STARS3",
            "TNS": "TNS2",
            "TWD": "TWD2",
            "WHALE": "WHALE3",
            "WTUST": "UST3",
        }
        if self.ticker == TICKER_LUNA1:
            remap["LUNA"] = "LUNA2"  # Terra Classic
        elif self.ticker == TICKER_LUNA2:
            remap["LUNA"] = "LUNA3"  # Terra v2

        if currency and currency.upper() in remap:
            return remap[currency.upper()]
        return currency

    def _cointracker_code(self, currency):
        return currency

    def _cointracker_timestamp(self, ts):
        # Convert "2021-08-04 15:25:43" to "08/14/2021 15:25:43"
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

        return dt.strftime("%m/%d/%Y %H:%M:%S")

    def export_balances_csv(self, csvpath, truncate=None):
        self.sort_rows(reverse=False)

        # Find all currencies
        currencies = set()
        for row in self.rows:
            if row.received_currency:
                currencies.add(row.received_currency)
            if row.sent_currency:
                currencies.add(row.sent_currency)
            if row.fee_currency:
                currencies.add(row.fee_currency)

        # Initialize balance of each currency to zero at beginning
        balances = {}
        for currency in currencies:
            balances[currency] = 0

        # Create table array that represents new csv
        currencies_list = sorted(list(currencies))
        table = []

        # For each original row, create a corresponding row with all currency balances.
        for row in self.rows:
            if row.received_currency and row.received_amount:
                balances[row.received_currency] += float(row.received_amount)
            if row.sent_currency and row.sent_amount:
                balances[row.sent_currency] -= float(row.sent_amount)
            if row.fee_currency and row.fee:
                balances[row.fee_currency] -= float(row.fee)

            balance_row = [row.timestamp, row.txid]
            for currency in currencies_list:
                balance_row.append(balances[currency])

            table.append(balance_row)

        table.reverse()

        if truncate:
            table = table[:truncate]

        # Add header row to beginning of array
        header_row = ["timestamp", "txid"]
        header_row.extend(currencies_list)
        table.insert(0, header_row)

        # Write table array to csv
        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)
            mywriter.writerows(table)
            logging.info("Wrote to %s", csvpath)
