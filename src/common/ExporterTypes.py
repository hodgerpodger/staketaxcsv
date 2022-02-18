# CSV formats
FORMAT_DEFAULT = "default"
FORMAT_BALANCES = "balances"
FORMAT_ACCOINTING = "accointing"
FORMAT_COINTRACKING = "cointracking"
FORMAT_COINTRACKER = "cointracker"
FORMAT_CRYPTOTAXCALCULATOR = "cryptotaxcalculator"
FORMAT_KOINLY = "koinly"
FORMAT_TAXBIT = "taxbit"
FORMAT_TOKENTAX = "tokentax"
FORMAT_ZENLEDGER = "zenledger"
FORMATS = [
    FORMAT_DEFAULT,
    FORMAT_BALANCES,
    FORMAT_ACCOINTING,
    FORMAT_COINTRACKING,
    FORMAT_COINTRACKER,
    FORMAT_CRYPTOTAXCALCULATOR,
    FORMAT_KOINLY,
    FORMAT_TAXBIT,
    FORMAT_TOKENTAX,
    FORMAT_ZENLEDGER
]

#

# Note: TX_TYPE=_* means transaction is not included in non-default CSVs
# (i.e. _STAKING_DELEGATE is not included in koinly, cointracking, ... )

# ### COMMON ##########################################################################################

# Common exportable transactions
TX_TYPE_STAKING = "STAKING"  # Staking reward
TX_TYPE_AIRDROP = "AIRDROP"
TX_TYPE_TRADE = "TRADE"
TX_TYPE_TRANSFER = "TRANSFER"
TX_TYPE_SPEND = "SPEND"
TX_TYPE_INCOME = "INCOME"
TX_TYPE_BORROW = "BORROW"
TX_TYPE_REPAY = "REPAY"

# Common non-exportable transactions
TX_TYPE_LP_DEPOSIT = "_LP_DEPOSIT"
TX_TYPE_LP_WITHDRAW = "_LP_WITHDRAW"
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

# mirror protocol borrow
TX_TYPE_AUCTION = "_AUCTION"

# mirror protocol lp
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

# anchor liquidate
TX_TYPE_LIQUIDATE_COLLATERAL = "_LIQUIDATE_COLLATERAL"
TX_TYPE_SUBMIT_BID = "_SUBMIT_BID"
TX_TYPE_RETRACT_BID = "_RETRACT_BID"

# LOTA
TX_TYPE_LOTA_UNKNOWN = "_LOTA_UNKNOWN"

# SPEC
TX_TYPE_SPEC_UNKNOWN = "_SPEC_UNKNOWN"

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
TX_TYPE_SOL_TRANSFER_SELF = "_TRANSFER_SELF"
TX_TYPE_SOL_WORMHOLE_NOOP = "_WORMHOLE_NOOP"

# ### OSMO ##########################################################################################

TX_TYPE_OSMO_VOTE = "_VOTE"
TX_TYPE_OSMO_WITHDRAW_DELEGATOR_REWARD = "_WITHDRAW_DELEGATOR_REWARD"
TX_TYPE_OSMO_WITHDRAW_COMMISSION = "_WITHDRAW_COMMISSION"
TX_TYPE_OSMO_SET_WITHDRAW_ADDRESS = "_SET_WITHDRAW_ADDRESS"
TX_TYPE_OSMO_SUBMIT_PROPOSAL = "_SUBMIT_PROPOSAL"
TX_TYPE_OSMO_DEPOSIT = "_DEPOSIT"

################################################################################################

# Types included for all CSVs (i.e. koinly, cointracking, etc).
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

# taxbit fields
TAXBIT_FIELD_DATE_AND_TIME = "Date and Time"
TAXBIT_FIELD_TRANSACTION_TYPE = "Transaction Type"
TAXBIT_FIELD_SENT_QUANTITY = "Sent Quantity"
TAXBIT_FIELD_SENT_CURRENCY = "Sent Currency"
TAXBIT_FIELD_SENDING_SOURCE = "Sending Source"
TAXBIT_FIELD_RECEIVED_QUANTITY = "Received Quantity"
TAXBIT_FIELD_RECEIVED_CURRENCY = "Received Currency"
TAXBIT_FIELD_RECEIVING_DESTINATION = "Receiving Destination"
TAXBIT_FIELD_FEE = "Fee"
TAXBIT_FIELD_FEE_CURRENCY = "Fee Currency"
TAXBIT_FIELD_EXCHANGE_TRANSACTION_ID = "Exchange Transaction ID"
TAXBIT_FIELD_BLOCKCHAIN_TRANSACTION_HASH = "Blockchain Transaction Hash"
TAXBIT_FIELDS = [
    TAXBIT_FIELD_DATE_AND_TIME,
    TAXBIT_FIELD_TRANSACTION_TYPE,
    TAXBIT_FIELD_SENT_QUANTITY,
    TAXBIT_FIELD_SENT_CURRENCY,
    TAXBIT_FIELD_SENDING_SOURCE,
    TAXBIT_FIELD_RECEIVED_QUANTITY,
    TAXBIT_FIELD_RECEIVED_CURRENCY,
    TAXBIT_FIELD_RECEIVING_DESTINATION,
    TAXBIT_FIELD_FEE,
    TAXBIT_FIELD_FEE_CURRENCY,
    TAXBIT_FIELD_EXCHANGE_TRANSACTION_ID,
    TAXBIT_FIELD_BLOCKCHAIN_TRANSACTION_HASH
]
