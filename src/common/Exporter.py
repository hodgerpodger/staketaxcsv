
import csv
from datetime import datetime
import logging
import io
from pytz import timezone
import pytz
from tabulate import tabulate
import pandas as pd

# Note: TX_TYPE=_* means transaction is not included in non-default CSVs
# (i.e. _STAKING_DELEGATE is not included in koinly, cointracking, ... )

# ### COMMON ##########################################################################################

# Common exportable transactions
TX_TYPE_STAKING = "STAKING"  # Staking transaction with income
TX_TYPE_AIRDROP = "AIRDROP"
TX_TYPE_TRADE = "TRADE"
TX_TYPE_TRANSFER = "TRANSFER"
TX_TYPE_SPEND = "SPEND"
TX_TYPE_INCOME = "INCOME"
TX_TYPE_BORROW = "BORROW"
TX_TYPE_REPAY = "REPAY"

# Common non-exportable transactions
TX_TYPE_UNKNOWN = "_UNKNOWN"
TX_TYPE_UNKNOWN_ERROR = "_UNKNOWN_ERROR"
TX_TYPE_STAKING_DELEGATE = "_STAKING_DELEGATE"
TX_TYPE_STAKING_UNDELEGATE = "_STAKING_UNDELEGATE"
TX_TYPE_STAKING_REDELEGATE = "_STAKING_REDELEGATE"
TX_TYPE_STAKING_WITHDRAW_REWARD = "_STAKING_WITHDRAW_REWARD"

# ### LUNA ##########################################################################################

TX_TYPE_VOTE = "_VOTE"
TX_TYPE_GOV = "_GOV"
TX_TYPE_GOV_STAKE = "_GOV_STAKE"
TX_TYPE_GOV_UNSTAKE = "_GOV_UNSTAKE"

# mirror protocol lp
TX_TYPE_LP_DEPOSIT = "_LP_DEPOSIT"
TX_TYPE_LP_WITHDRAW = "_LP_WITHDRAW"
TX_TYPE_LP_STAKE = "_LP_STAKE"
TX_TYPE_LP_UNSTAKE = "_LP_UNSTAKE"

# anchor earn
TX_TYPE_EARN_DEPOSIT = "_EARN_DEPOSIT"
TX_TYPE_EARN_WITHDRAW = "_EARN_WITHDRAW"

# anchor bond
TX_TYPE_BOND = "_BOND"
TX_TYPE_UNBOND = "_UNBOND"
TX_TYPE_UNBOND_WITHDRAW = "_UNBOND_WITHDRAW"
TX_TYPE_UNBOND_INSTANT = "_UNBOND_INSTANT"

# anchor borrow
TX_TYPE_DEPOSIT_COLLATERAL = "_DEPOSIT_COLLATERAL"
TX_TYPE_WITHDRAW_COLLATERAL = "_WITHDRAW_COLLATERAL"
# borrow/repay in "common exportable transactions"

# LOTA
TX_TYPE_LOTA_UNKNOWN = "_LOTA_UNKNOWN"

# nft
TX_TYPE_NFT_WHITELIST = "_NFT_WHITELIST"
TX_TYPE_NFT_MINT = "_NFT_MINT"
TX_TYPE_NFT_OFFER_SELL = "_NFT_OFFER_SELL"
TX_TYPE_NFT_WITHDRAW = "_NFT_WITHDRAW"
TX_TYPE_NFT_DEPOSIT = "_NFT_DEPOSIT"

# ### SOL ##########################################################################################

TX_TYPE_SOL_STAKING_SPLIT = "_STAKING_SPLIT"
TX_TYPE_SOL_STAKING_WITHDRAW = "_STAKING_WITHDRAW"
TX_TYPE_SOL_STAKING_DEACTIVATE = "_STAKING_DEACTIVATE"
TX_TYPE_SOL_STAKING_CREATE = "_STAKING_CREATE"
TX_TYPE_SOL_INIT_ACCOUNT = "_INIT_ACCOUNT"
TX_TYPE_SOL_CLOSE_ACCOUNT = "_CLOSE_ACCOUNT"
TX_TYPE_SOL_SETTLE_FUNDS = "_SETTLE_FUNDS"
TX_TYPE_MISSING_TIMESTAMP = "_ERROR"

TX_TYPE_SOL_LP_DEPOSIT = "_LP_DEPOSIT"
TX_TYPE_SOL_LP_WITHDRAW = "_LP_WITHDRAW"
TX_TYPE_SOL_LP_FARM = "_LP_FARM"
TX_TYPE_SOL_STAKE = "_STAKE"               # Ray stake, LP stake, etc. (not Solana stake)
TX_TYPE_SOL_UNSTAKE = "_UNSTAKE"           # Ray unstake
TX_TYPE_SOL_REWARD_ZERO = "_REWARD_ZERO"   # Ray staking reward 0
TX_TYPE_SOL_SERUM_DEX = "_SERUM_DEX"

# ### OSMO ##########################################################################################

TX_TYPE_OSMO_VOTE = "_VOTE"

################################################################################################

# Types included for all non-default CSVs (i.e. koinly, cointracking, etc).
TX_TYPES_CSVEXPORT = [
    TX_TYPE_STAKING,
    TX_TYPE_AIRDROP,
    TX_TYPE_TRADE,
    TX_TYPE_SPEND,
    TX_TYPE_INCOME,
    TX_TYPE_TRANSFER,
    TX_TYPE_BORROW,
    TX_TYPE_REPAY
]

# Types with taxable=True
TX_TYPES_TAXABLE = [
    TX_TYPE_STAKING,
    TX_TYPE_AIRDROP,
    TX_TYPE_TRADE,
    TX_TYPE_SPEND,
    TX_TYPE_INCOME
]

# stake.tax csv format
ROW_FIELDS = [
    "timestamp", "tx_type", "taxable", "received_amount", "received_currency",
    "sent_amount", "sent_currency", "fee", "fee_currency", "comment", "txid",
    "url", "exchange", "wallet_address"
]

# fields used for unit testing
TEST_ROW_FIELDS = ["timestamp", "tx_type", "taxable", "received_amount", "received_currency",
                   "sent_amount", "sent_currency", "fee", "fee_currency", "txid"]

# cointracking csv format: https://cointracking.info/import/import_csv/
CT_FIELD_TYPE = "Type"
CT_FIELD_BUY_AMOUNT = "Buy Amount"
CT_FIELD_BUY_CURRENCY = "Buy Currency"
CT_FIELD_SELL_AMOUNT = "Sell Amount"
CT_FIELD_SELL_CURRENCY = "Sell Currency"
CT_FIELD_FEE = "Fee"
CT_FIELD_FEE_CURRENCY = "Fee Currency"
CT_FIELD_EXCHANGE = "Exchange"
CT_FIELD_TRADE_GROUP = "Trade-Group"
CT_FIELD_COMMENT = "Comment"
CT_FIELD_DATE = "Date"
CT_FIELD_TXID = "Tx-ID"
CT_FIELDS = [
    CT_FIELD_TYPE, CT_FIELD_BUY_AMOUNT, CT_FIELD_BUY_CURRENCY, CT_FIELD_SELL_AMOUNT, CT_FIELD_SELL_CURRENCY,
    CT_FIELD_FEE, CT_FIELD_FEE_CURRENCY, CT_FIELD_EXCHANGE, CT_FIELD_TRADE_GROUP, CT_FIELD_COMMENT, CT_FIELD_DATE,
    CT_FIELD_TXID
]

# tokentax csv format
TT_FIELD_TYPE = "Type"
TT_FIELD_BUY_AMOUNT = "BuyAmount"
TT_FIELD_BUY_CURRENCY = "BuyCurrency"
TT_FIELD_SELL_AMOUNT = "SellAmount"
TT_FIELD_SELL_CURRENCY = "SellCurrency"
TT_FIELD_FEE_AMOUNT = "FeeAmount"
TT_FIELD_FEE_CURRENCY = "FeeCurrency"
TT_FIELD_EXCHANGE = "Exchange"
TT_FIELD_GROUP = "Group"
TT_FIELD_COMMENT = "Comment"
TT_FIELD_DATE = "Date"
TT_FIELDS = [
    TT_FIELD_TYPE,
    TT_FIELD_BUY_AMOUNT,
    TT_FIELD_BUY_CURRENCY,
    TT_FIELD_SELL_AMOUNT,
    TT_FIELD_SELL_CURRENCY,
    TT_FIELD_FEE_AMOUNT,
    TT_FIELD_FEE_CURRENCY,
    TT_FIELD_EXCHANGE,
    TT_FIELD_GROUP,
    TT_FIELD_COMMENT,
    TT_FIELD_DATE
]

# cointracker format
CR_FIELD_DATE = "Date"
CR_FIELD_RECEIVED_QUANTITY = "Received Quantity"
CR_FIELD_RECEIVED_CURRENCY = "Received Currency"
CR_FIELD_SENT_QUANTITY = "Sent Quantity"
CR_FIELD_SENT_CURRENCY = "Sent Currency"
CR_FIELD_FEE_AMOUNT = "Fee Amount"
CR_FIELD_FEE_CURRENCY = "Fee Currency"
CR_FIELD_TAG = "Tag"
CR_FIELD_TRANSACTION_ID = "Transaction ID"  # Not real field.  Added for user danb
CR_FIELDS = [
    CR_FIELD_DATE, CR_FIELD_RECEIVED_QUANTITY, CR_FIELD_RECEIVED_CURRENCY,
    CR_FIELD_SENT_QUANTITY, CR_FIELD_SENT_CURRENCY, CR_FIELD_FEE_AMOUNT,
    CR_FIELD_FEE_CURRENCY, CR_FIELD_TAG, CR_FIELD_TRANSACTION_ID
]

# koinly format
KOINLY_FIELD_DATE = "Date"
KOINLY_FIELD_SENT_AMOUNT = "Sent Amount"
KOINLY_FIELD_SENT_CURRENCY = "Sent Currency"
KOINLY_FIELD_RECEIVED_AMOUNT = "Received Amount"
KOINLY_FIELD_RECEIVED_CURRENCY = "Received Currency"
KOINLY_FIELD_FEE_AMOUNT = "Fee Amount"
KOINLY_FIELD_FEE_CURRENCY = "Fee Currency"
KOINLY_FIELD_NET_WORTH_AMOUNT = "Net Worth Amount"
KOINLY_FIELD_NET_WORTH_CURRENCY = "Net Worth Currency"
KOINLY_FIELD_LABEL = "Label"
KOINLY_FIELD_DESCRIPTION = "Description"
KOINLY_FIELD_TXHASH = "TxHash"
KOINLY_FIELDS = [
    KOINLY_FIELD_DATE,
    KOINLY_FIELD_SENT_AMOUNT,
    KOINLY_FIELD_SENT_CURRENCY,
    KOINLY_FIELD_RECEIVED_AMOUNT,
    KOINLY_FIELD_RECEIVED_CURRENCY,
    KOINLY_FIELD_FEE_AMOUNT,
    KOINLY_FIELD_FEE_CURRENCY,
    KOINLY_FIELD_NET_WORTH_AMOUNT,
    KOINLY_FIELD_NET_WORTH_CURRENCY,
    KOINLY_FIELD_LABEL,
    KOINLY_FIELD_DESCRIPTION,
    KOINLY_FIELD_TXHASH
]

# cryptotaxcalculator.io format
CALC_FIELD_TIMESTAMP = "Timestamp (UTC)"
CALC_FIELD_TYPE = "Type"
CALC_FIELD_BASE_CURRENCY = "Base Currency (Optional)"
CALC_FIELD_BASE_AMOUNT = "Base Amount (Optional)"
CALC_FIELD_QUOTE_CURRENCY = "Quote Currency (Optional)"
CALC_FIELD_QUOTE_AMOUNT = "Quote Amount (Optional)"
CALC_FIELD_FEE_CURRENCY = "Fee Currency (Optional)"
CALC_FIELD_FEE_AMOUNT = "Fee Amount (Optional)"
CALC_FIELD_FROM = "From (Optional)"
CALC_FIELD_TO = "To (Optional)"
CALC_FIELD_ID = "ID (Optional)"
CALC_FIELD_DESCRIPTION = "Description (Optional)"
CALC_FIELDS = [
    CALC_FIELD_TIMESTAMP,
    CALC_FIELD_TYPE,
    CALC_FIELD_BASE_CURRENCY,
    CALC_FIELD_BASE_AMOUNT,
    CALC_FIELD_QUOTE_CURRENCY,
    CALC_FIELD_QUOTE_AMOUNT,
    CALC_FIELD_FEE_CURRENCY,
    CALC_FIELD_FEE_AMOUNT,
    CALC_FIELD_FROM,
    CALC_FIELD_TO,
    CALC_FIELD_ID,
    CALC_FIELD_DESCRIPTION
]

# accointing .xlsl fields
ACCOINT_FIELD_TRANSACTION_TYPE = "transactionType"
ACCOINT_FIELD_DATE = "date"
ACCOINT_FIELD_IN_BUY_AMOUNT = "inBuyAmount"
ACCOINT_FIELD_IN_BUY_ASSET = "inBuyAsset"
ACCOINT_FIELD_OUT_SELL_AMOUNT = "outSellAmount"
ACCOINT_FIELD_OUT_SELL_ASSET = "outSellAsset"
ACCOINT_FIELD_FEE_AMOUNT = "feeAmount (optional)"
ACCOINT_FIELD_FEE_ASSET = "feeAsset (optional)"
ACCOINT_FIELD_CLASSIFICATION = "classification (optional)"
ACCOINT_FIELD_OPERATION_ID = "operationId (optional)"
ACCOINT_FIELDS = [
    ACCOINT_FIELD_TRANSACTION_TYPE,
    ACCOINT_FIELD_DATE,
    ACCOINT_FIELD_IN_BUY_AMOUNT,
    ACCOINT_FIELD_IN_BUY_ASSET,
    ACCOINT_FIELD_OUT_SELL_AMOUNT,
    ACCOINT_FIELD_OUT_SELL_ASSET,
    ACCOINT_FIELD_FEE_AMOUNT,
    ACCOINT_FIELD_FEE_ASSET,
    ACCOINT_FIELD_CLASSIFICATION,
    ACCOINT_FIELD_OPERATION_ID
]

# zenledger fields
ZEN_FIELD_TIMESTAMP = "Timestamp"
ZEN_FIELD_TYPE = "Type"
ZEN_FIELD_IN_AMOUNT = "IN Amount"
ZEN_FIELD_IN_CURRENCY = "IN Currency"
ZEN_FIELD_OUT_AMOUNT = "Out Amount"
ZEN_FIELD_OUT_CURRENCY = "Out Currency"
ZEN_FIELD_FEE_AMOUNT = "Fee Amount"
ZEN_FIELD_FEE_CURRENCY = "Fee Currency"
ZEN_FIELD_EXCHANGE = "Exchange(optional)"
ZEN_FIELD_US_BASED = "US Based"
ZEN_FIELDS = [
    ZEN_FIELD_TIMESTAMP,
    ZEN_FIELD_TYPE,
    ZEN_FIELD_IN_AMOUNT,
    ZEN_FIELD_IN_CURRENCY,
    ZEN_FIELD_OUT_AMOUNT,
    ZEN_FIELD_OUT_CURRENCY,
    ZEN_FIELD_FEE_AMOUNT,
    ZEN_FIELD_FEE_CURRENCY,
    ZEN_FIELD_EXCHANGE,
    ZEN_FIELD_US_BASED
]


class Row:

    def __init__(self, timestamp, tx_type, received_amount, received_currency, sent_amount, sent_currency, fee, fee_currency,
                 exchange, wallet_address, txid, url="", z_index=0, comment=""):
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

        # Use None instead of "False", so that it is consistent with what is shown to user
        self.taxable = True if (self.tx_type in TX_TYPES_TAXABLE) else None

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
            self.taxable,
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
            self.taxable,
            self.received_amount,
            self.received_currency,
            self.sent_amount,
            self.sent_currency,
            self.fee,
            self.fee_currency,
            self.txid
        ]


class Exporter:

    def __init__(self, wallet_address):
        self.wallet_address = wallet_address
        self.rows = []
        self.reverse = None  # last sorted direction

    def ingest_row(self, row):
        self.rows.append(row)

    def sort_rows(self, reverse=True):
        if self.reverse != reverse:
            self.rows.sort(key=lambda row: (row.timestamp, row.z_index), reverse=reverse)

    def _rows_export(self):
        return filter(lambda row: row.tx_type in TX_TYPES_CSVEXPORT, self.rows)

    def export_print(self):
        """ Prints transactions """
        print("Transactions:")
        print(self.export_string())

    def export_string(self):
        table = [ROW_FIELDS]
        table.extend([row.as_array() for row in self.rows])
        return tabulate(table)

    def export_for_test(self):
        table = [TEST_ROW_FIELDS]
        table.extend([row.as_array_short() for row in self.rows])

        return tabulate(table)

    def export_default_csv(self, csvpath=None, truncate=0):
        self.sort_rows(reverse=True)

        rows = self.rows
        table = [ROW_FIELDS]
        if truncate:
            table.extend([row.as_array() for row in rows[0:truncate]])
        else:
            table.extend([row.as_array() for row in rows])

        if csvpath:
            with open(csvpath, 'w') as f:
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
            TX_TYPE_AIRDROP: "Airdrop",
            TX_TYPE_STAKING: "Staking",
            TX_TYPE_TRADE: "Trade",
            TX_TYPE_TRANSFER: "Transfer",
            TX_TYPE_INCOME: "Income",
            TX_TYPE_SPEND: "Spend",
            TX_TYPE_BORROW: "Transfer",
            TX_TYPE_REPAY: "Transfer"
        }

        self.sort_rows(reverse=True)
        rows = self._rows_export()

        with open(csvpath, 'w') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(CT_FIELDS)

            # data rows
            for row in rows:
                tx_type = cointracking_types[row.tx_type]
                if tx_type == "Transfer":
                    if row.received_amount and not row.sent_amount:
                        tx_type = "Deposit"
                    elif row.sent_amount and not row.received_amount:
                        tx_type = "Withdrawal"
                    else:
                        tx_type = "Deposit"
                        logging.error("Bad condition in export_cointracking_csv(): {}, {}, {}".format(
                            row.received_amount, row.sent_amount, row.as_array()))

                txid_cointracking = str(row.txid) + "." + str(row.received_currency) + "." + str(row.sent_currency)

                if row.comment:
                    comment = "{} {}".format(row.comment, row.txid)
                else:
                    comment = row.txid

                line = [
                    tx_type,                                             # "Staking" | "Airdrop" | "Trade
                    row.received_amount,                                 # Buy Amount
                    self._cointracking_code(row.received_currency),      # Buy Currency
                    row.sent_amount,                                     # Sell Amount
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

        logging.info("Wrote to %s", csvpath)

    def export_tokentax_csv(self, csvpath):
        """ Write CSV, suitable for import into TokenTax """
        tokentax_types = {
            TX_TYPE_AIRDROP: "Airdrop",
            TX_TYPE_STAKING: "Staking",
            TX_TYPE_TRADE: "Trade",
            TX_TYPE_TRANSFER: "Transfer",
            TX_TYPE_INCOME: "Income",
            TX_TYPE_SPEND: "Spend",
            TX_TYPE_BORROW: "Transfer",
            TX_TYPE_REPAY: "Transfer"
        }

        self.sort_rows(reverse=True)
        rows = self._rows_export()

        with open(csvpath, 'w') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(TT_FIELDS)

            # data rows
            for row in rows:
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
            TX_TYPE_AIRDROP: "airdrop",
            TX_TYPE_STAKING: "staked",
            TX_TYPE_TRADE: "",
            TX_TYPE_TRANSFER: "",
            TX_TYPE_INCOME: "payment",
            TX_TYPE_SPEND: "",
            TX_TYPE_BORROW: "",
            TX_TYPE_REPAY: ""
        }

        self.sort_rows(reverse=True)
        rows = self._rows_export()

        with open(csvpath, 'w') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(CR_FIELDS)

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
        self.sort_rows(reverse=True)
        rows = self._rows_export()

        with open(csvpath, 'w') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(KOINLY_FIELDS)

            # data rows
            for row in rows:
                if row.tx_type == TX_TYPE_TRADE:
                    label = ""
                elif row.tx_type == TX_TYPE_AIRDROP:
                    label = "airdrop"
                elif row.tx_type == TX_TYPE_STAKING:
                    label = "staking"
                elif row.tx_type == TX_TYPE_INCOME:
                    label = "other income"
                elif row.tx_type == TX_TYPE_SPEND:
                    label = "cost"
                elif row.tx_type == TX_TYPE_BORROW:
                    label = ""
                elif row.tx_type == TX_TYPE_REPAY:
                    label = ""
                elif row.tx_type == TX_TYPE_TRANSFER:
                    label = ""
                else:
                    label = ""
                    logging.error("koinly: unable to handle tx_type=%s", row.tx_type)

                line = [
                    row.timestamp,                                       # Date
                    row.sent_amount,                                     # Sent Amount
                    row.sent_currency,                                   # Sent Currency
                    row.received_amount,                                 # Received Amount
                    row.received_currency,                               # Received Currency
                    row.fee,                                             # Fee Amount
                    row.fee_currency,                                    # Fee Currency
                    "",                                                  # Net Worth Amount
                    "",                                                  # Net Worth Currency
                    label,                                               # Label
                    row.comment,                                         # Description
                    row.txid                                             # TxHash
                ]
                mywriter.writerow(line)

        logging.info("Wrote to %s", csvpath)

    def export_calculator_csv(self, csvpath):
        """ Write CSV, suitable for import into cryptataxcalculator.io """
        self.sort_rows(reverse=True)
        rows = self._rows_export()

        with open(csvpath, 'w') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(CALC_FIELDS)

            # data rows
            for row in rows:
                # Determine type field
                if row.tx_type == TX_TYPE_STAKING:
                    type = "interest"
                elif row.tx_type == TX_TYPE_AIRDROP:
                    type = "airdrop"
                elif row.tx_type == TX_TYPE_TRADE:
                    type = "sell"
                elif row.tx_type == TX_TYPE_TRANSFER:
                    if row.received_amount:
                        type = "transfer-in"
                    elif row.sent_amount:
                        type = "transfer-out"
                elif row.tx_type == TX_TYPE_INCOME:
                    type = "income"
                elif row.tx_type == TX_TYPE_SPEND:
                    type = "sell"
                elif row.tx_type == TX_TYPE_BORROW:
                    type = "borrow"
                elif row.tx_type == TX_TYPE_REPAY:
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
        """ Writes CSV, suitable for import into Accointing """
        self.sort_rows(reverse=True)

        rows = self._rows_export()
        with open(csvpath, 'w') as f:
            mywriter = csv.writer(f)
            mywriter.writerow(ACCOINT_FIELDS)

            for row in rows:
                # Write one line to CSV

                # Determine transaction_type, classification
                if row.tx_type == TX_TYPE_STAKING:
                    transaction_type = "deposit"
                    classification = "staked"
                elif row.tx_type == TX_TYPE_AIRDROP:
                    transaction_type = "deposit"
                    classification = "airdrop"
                elif row.tx_type == TX_TYPE_TRADE:
                    transaction_type = "order"
                    classification = ""
                elif row.tx_type == TX_TYPE_SPEND:
                    transaction_type = "withdraw"
                    classification = "payment"
                elif row.tx_type == TX_TYPE_TRANSFER:
                    if row.sent_amount:
                        transaction_type = "withdraw"
                    elif row.received_amount:
                        transaction_type = "deposit"
                    else:
                        transaction_type = ""
                        logging.error("Bad condition for transfer")
                    classification = ""
                elif row.tx_type == TX_TYPE_INCOME:
                    transaction_type = "deposit"
                    classification = "income"
                elif row.tx_type == TX_TYPE_BORROW:
                    transaction_type = "deposit"
                    classification = ""
                elif row.tx_type == TX_TYPE_REPAY:
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
            TX_TYPE_AIRDROP: "airdrop",
            TX_TYPE_STAKING: "staking",
            TX_TYPE_TRADE: "Trade",
            TX_TYPE_TRANSFER: "transfer",
            TX_TYPE_INCOME: "misc reward",
            TX_TYPE_SPEND: "payment",
            TX_TYPE_BORROW: "transfer",
            TX_TYPE_REPAY: "transfer"
        }

        self.sort_rows(reverse=True)
        rows = self._rows_export()

        with open(csvpath, 'w') as f:
            mywriter = csv.writer(f)

            # header row
            mywriter.writerow(ZEN_FIELDS)

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
        with open(csvpath, 'w') as f:
            mywriter = csv.writer(f)
            mywriter.writerows(table)
            logging.info("Wrote to %s", csvpath)
