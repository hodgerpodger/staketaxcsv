
import logging
from datetime import datetime

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.algo.handle_amm import handle_swap, is_swap_group
from staketaxcsv.algo.handle_transfer import handle_transfer_transactions
from staketaxcsv.algo.transaction import is_app_call
from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.common.TxInfo import TxInfo


def get_group_transactions(groupid, start, transactions):
    group = []
    for tx in transactions[start:]:
        current_groupid = tx.get("group", None)
        if current_groupid != groupid:
            break
        group.append(tx)
    # Make sure the transactions are in the right order
    return sorted(group, key=lambda val: val["intra-round-offset"])


def get_group_txinfo(wallet_address, transaction):
    groupid = transaction["group"]
    txid = groupid
    timestamp = datetime.utcfromtimestamp(transaction["round-time"]).strftime('%Y-%m-%d %H:%M:%S')
    fee = Algo(0)
    url = f"https://explorer.perawallet.app/tx-group/{groupid}/"
    txinfo = TxInfo(txid, timestamp, fee, fee.ticker, wallet_address, co.EXCHANGE_ALGORAND_BLOCKCHAIN, url)

    return txinfo


def has_app_transactions(group):
    return any(is_app_call(tx) for tx in group)


def handle_transaction_group(wallet_address, dapps, group, exporter, txinfo):
    for app in dapps:
        try:
            if app.is_dapp_transaction(group):
                return app.handle_dapp_transaction(group, txinfo)
        except Exception as e:
            logging.error("Exception handling txid=%s with plugin=%s, exception=%s",
                          txinfo.txid, app.name, str(e))
            ErrorCounter.increment("exception", txinfo.txid)
            if localconfig.debug:
                raise (e)

    if is_swap_group(wallet_address, group):
        handle_swap(wallet_address, group, exporter, txinfo)
    else:
        if localconfig.debug and has_app_transactions(group):
            txinfo.comment = "Unknown App"
        handle_transfer_transactions(wallet_address, group, exporter, txinfo)
