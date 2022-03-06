import csv
import io
from datetime import datetime
import logging
import pandas as pd
import pytz
from pytz import timezone
from tabulate import tabulate
import re
import json

from algo.constants import EXCHANGE_ALGORAND_BLOCKCHAIN
from common import ExporterTypes as et
from sol.constants import EXCHANGE_SOLANA_BLOCKCHAIN
from common.exporter_koinly import NullMap


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

    def __init__(self, wallet_address, localconfig=None):
        self.wallet_address = wallet_address
        self.rows = []
        self.is_reverse = None  # last sorted direction

        self.lp_treatment = et.LP_TREATMENT_DEFAULT
        self.use_cache = False

        if localconfig:
            if hasattr(localconfig, "lp_treatment"):
                self.lp_treatment = localconfig.lp_treatment
            self.use_cache = localconfig.cache

    def ingest_row(self, row):
        self.rows.append(row)

    def sort_rows(self, reverse=True):
        if self.is_reverse != reverse:
            self.rows.sort(key=lambda row: (row.timestamp, row.z_index), reverse=reverse)
            self.is_reverse = reverse

    def _rows_export(self, format):
        self.sort_rows(reverse=True)
        rows = filter(lambda row: row.tx_type in et.TX_TYPES_CSVEXPORT, self.rows)

        if format == et.FORMAT_KOINLY:
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
        elif format == et.FORMAT_COINTRACKING:
            self.export_cointracking_csv(csvpath)
        elif format == et.FORMAT_COINTRACKER:
            self.export_cointracker_csv(csvpath)
        elif format == et.FORMAT_KOINLY:
            self.export_koinly_csv(csvpath)
        elif format == et.FORMAT_CRYPTOTAXCALCULATOR:
            self.export_calculator_csv(csvpath)
        elif format == et.FORMAT_ACCOINTING:
            self.export_accointing_csv(csvpath)
            xlsxpath = csvpath.replace(".csv", ".xlsx")
            self.convert_csv_to_xlsx(csvpath, xlsxpath)
            return xlsxpath
        elif format == et.FORMAT_TOKENTAX:
            self.export_tokentax_csv(csvpath)
        elif format == et.FORMAT_ZENLEDGER:
            self.export_zenledger_csv(csvpath)
        elif format == et.FORMAT_TAXBIT:
            self.export_taxbit_csv(csvpath)
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

    def export_koinly_csv(self, csvpath):
        """ Write CSV, suitable for import into Koinly """
        NullMap.load(self.use_cache)
        rows = self._rows_export(et.FORMAT_KOINLY)

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
        NullMap.flush(self.use_cache)

    def koinly_currency(self, currency):
        if self._is_koinly_lp(currency):
            return NullMap.get_null_symbol(currency)
        elif currency and currency.upper() == "PSI":
            # koinly default PSI is "Passive Income", not "Nexus Protocol" that we want
            return "ID:106376"
        elif currency and currency.upper() == "APOLLO":
            return "ID:28478"
        elif currency and currency.upper() == "ASTRO":
            return "ID:48993"
        else:
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

        with open(csvpath, 'w', newline='', encoding='utf-8') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(et.TAXBIT_FIELDS)

            # data rows

            if self.wallet_address.startswith("cosmo"):
                tx_source = "ATOM WALLET"
            elif self.wallet_address.startswith("terra"):
                tx_source = "LUNA WALLET"
            elif self.wallet_address.startswith("osmo"):
                tx_source = "OSMO WALLET"
            elif self.wallet_address.startswith("chihuahua"):
                tx_source = "HUAHUA WALLET"
            else:
                exchange = self.rows[0].exchange if len(self.rows) else ""
                if exchange == EXCHANGE_SOLANA_BLOCKCHAIN:
                    tx_source = "SOL WALLET"
                elif exchange == EXCHANGE_ALGORAND_BLOCKCHAIN:
                    tx_source = "ALGO WALLET"
                else:
                    tx_source = ""
                    logging.critical("Bad condition: unable to identify tx_source in export_taxbit_csv()")

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

    def _utc_to_local(self, date_string, timezone_string):
        dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        utc_dt = pytz.utc.localize(dt)
        local_tz = timezone(timezone_string)
        local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))

        return local_dt.strftime("%Y-%m-%d %H:%M:%S")

    def _cointracking_code(self, currency):
        if currency == "ANC":
            return "ANC2"
        if currency == "LUNA":
            return "LUNA2"
        if currency == "MIR":
            return "MIR2"
        if currency == "SOL":
            return "SOL2"
        if currency == "wtUST":
            return "UST3"
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
