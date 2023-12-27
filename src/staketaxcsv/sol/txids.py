import logging
from datetime import datetime, timezone

from staketaxcsv.sol.api_rpc import RpcAPI
from staketaxcsv.sol.config_sol import localconfig
ABSOLUTE_MAX_QUERIES = 500
LIMIT_PER_QUERY = 1000


def get_txids(wallet_address, progress, start_date=None, end_date=None):
    # Sometimes, transactions do not all appear under main wallet address when querying transaction history.
    # So retrieve token addresses too.
    addresses = [wallet_address]
    token_accounts = RpcAPI.fetch_token_accounts(wallet_address).keys()
    addresses.extend(token_accounts)

    out = get_txids_for_addresses(addresses, progress, start_date, end_date)
    return out


def get_txids_for_addresses(addresses, progress, start_date=None, end_date=None):
    """ Returns transactions txids for all addresses in one list """
    start_ts = _unix_timestamp(start_date + " 00:00:00") if start_date else None
    end_ts = _unix_timestamp(end_date + " 23:59:59") if end_date else None

    out = []
    txids_seen = set()
    for i, address in enumerate(addresses):
        if progress and i % 10 == 0:
            message = f"Fetched txids for {i} of {len(addresses)} addresses..."
            progress.report_message(message)

        # main wallet address: use max txs limit
        # associated token accounts: use lower txs limit based off max txs limit
        if i == 0:
            max_txs = localconfig.limit
        else:
            max_txs = int(localconfig.limit / 10)

        # Get transaction txids for this token account
        before_txid = None
        keep_fetching = True
        for j in range(ABSOLUTE_MAX_QUERIES):
            logging.info("query %s for address=%s", j, address)
            txids, before_txid = RpcAPI.get_txids(address, limit=LIMIT_PER_QUERY, before_txid=before_txid)

            for txid, block_time in txids:
                # Handle case of block_time=None for old old tx without timestamp
                if block_time is None:
                    block_time = _unix_timestamp("2020-01-01 00:00:00")

                # Check if txid is within the time range
                if (start_date is None or block_time >= start_ts) and (end_date is None or block_time <= end_ts):
                    if txid not in txids_seen:
                        out.append(txid)
                        txids_seen.add(txid)

                if start_date is not None and block_time < start_ts:
                    keep_fetching = False
                    break

            # No more transactions
            if before_txid is None:
                keep_fetching = False
            # Reached max transaction limit
            if len(txids) > max_txs:
                keep_fetching = False

            if not keep_fetching:
                break

    # Process oldest first
    out.reverse()
    return out


def _unix_timestamp(dt_str):
    if dt_str:
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    return None
