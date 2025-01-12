
import logging
from collections import defaultdict
from staketaxcsv.common.BalExporter import BalExporter
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.sol.api_rpc import RpcAPI
from staketaxcsv.sol.txids import get_txids
from staketaxcsv.sol.TxInfoSol import WalletInfo
from staketaxcsv.sol.processor import process_tx
from staketaxcsv.sol.config_sol import localconfig
from staketaxcsv.settings_csv import TICKER_SOL


def balances_history(wallet_address, start_date=None, end_date=None):
    """
    Writes historical balances CSV rows to BalExporter object,
    combining main wallet and staking account balances into a cumulative sum.
    Transactions are sorted chronologically by their timestamps.
    """
    balances = defaultdict(lambda: defaultdict(dict))  # {timestamp: {address: {currency: balance}}}

    # Process main account transactions
    logging.info("Processing main account transactions for wallet: %s", wallet_address)
    wallet_info = WalletInfo(wallet_address)
    _process_address(wallet_address, wallet_info, balances, start_date, end_date)

    # Process staking accounts' transactions
    logging.info("Processing staking account transactions...")
    for staking_address in wallet_info.get_staking_addresses():
        logging.info("Processing staking account: %s", staking_address)
        staking_wallet_info = WalletInfo(staking_address)
        _process_address(staking_address, staking_wallet_info, balances, start_date, end_date)

    # Combine and export balances
    bal_exporter = BalExporter(wallet_address)
    _export_combined_balances(balances, bal_exporter)

    return bal_exporter


def _process_address(address, wallet_info, balances, start_date, end_date):
    """
    Processes transactions for a single address and records balance updates.
    """
    dummy_exporter = Exporter(address, localconfig, TICKER_SOL)
    logging.info("roger process for address=%s", address)
    txids = get_txids(address, None, start_date, end_date)

    for i, txid in enumerate(txids):
        elem = RpcAPI.fetch_tx(txid)

        txinfo = process_tx(wallet_info, dummy_exporter, txid, elem)

        if txinfo:
            _record_balance_update(txinfo, balances)


def _record_balance_update(txinfo, balances):
    """
    Records a balance update for a given transaction info.
    """
    timestamp = txinfo.timestamp
    addr = txinfo.wallet_address

    # Process balances for each account in the transaction
    for currency, balance in txinfo.wallet_balances.items():
        if len(currency) <= 16:  # Omit unknown symbols to simplify
            balances[timestamp][addr][currency] = balance


def _export_combined_balances(balances, bal_exporter):
    """
    Exports balances chronologically:
    1. Accumulates combined balances across accounts for all timestamps.
    2. Only includes entries in the row for currencies with original data at that timestamp.
    """
    # Sort timestamps to process in chronological order
    sorted_timestamps = sorted(balances.keys())

    # Track cumulative balances
    cumulative_balances = defaultdict(float)  # {currency: total_balance}
    latest_account_balances = defaultdict(lambda: defaultdict(float))  # {address: {currency: balance}}

    for timestamp in sorted_timestamps:
        row_data = {}

        # Update account balances and cumulative balances for the current timestamp
        for address, account_balances in balances[timestamp].items():
            for currency, balance in account_balances.items():
                # Update cumulative totals
                cumulative_balances[currency] += balance - latest_account_balances[address][currency]
                # Update the latest known balance for this account and currency
                latest_account_balances[address][currency] = balance
                # Include the original data for this currency in the current row
                row_data[currency] = cumulative_balances[currency]

        # Ingest the row into BalExporter (only currencies with updates at this timestamp)
        bal_exporter.ingest_row(timestamp, row_data)
