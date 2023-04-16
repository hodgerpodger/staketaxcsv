
import logging
import urllib.parse
from datetime import datetime

from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.algo.handle_akita import handle_akita_swap_transaction, is_akita_swap_transaction
from staketaxcsv.algo.handle_algodex import handle_algodex_transaction, is_algodex_transaction
from staketaxcsv.algo.handle_amm import handle_swap, is_swap_group
from staketaxcsv.algo.handle_gard import handle_gard_transaction, is_gard_transaction
from staketaxcsv.algo.handle_transfer import (
    handle_governance_reward_transaction,
    handle_transfer_transactions,
    is_governance_reward_transaction,
)
from staketaxcsv.algo.handle_wagmiswap import handle_wagmiswap_transaction, is_wagmiswap_transaction
from staketaxcsv.algo.handle_yieldly import handle_yieldly_transaction, is_yieldly_transaction
from staketaxcsv.algo.transaction import is_transfer
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
    url = "https://algoexplorer.io/tx/group/{}".format(urllib.parse.quote_plus(groupid))
    txinfo = TxInfo(txid, timestamp, fee, fee.ticker, wallet_address, co.EXCHANGE_ALGORAND_BLOCKCHAIN, url)

    return txinfo


def has_only_transfer_transactions(group):
    return all(is_transfer(tx) for tx in group)


def has_app_transactions(group):
    return any(tx["tx-type"] == co.TRANSACTION_TYPE_APP_CALL for tx in group)


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

    if (is_governance_reward_transaction(wallet_address, group)):
        handle_governance_reward_transaction(group, exporter, txinfo)

    elif is_yieldly_transaction(group):
        handle_yieldly_transaction(group, exporter, txinfo)

    elif is_gard_transaction(wallet_address, group):
        handle_gard_transaction(wallet_address, group, exporter, txinfo)

    elif is_algodex_transaction(wallet_address, group):
        handle_algodex_transaction(wallet_address, group, exporter, txinfo)

    elif is_wagmiswap_transaction(group):
        handle_wagmiswap_transaction(wallet_address, group, exporter, txinfo)

    elif is_akita_swap_transaction(group):
        handle_akita_swap_transaction(group, exporter, txinfo)

    elif is_swap_group(wallet_address, group):
        handle_swap(wallet_address, group, exporter, txinfo)

    else:
        if localconfig.debug and has_app_transactions(group):
            txinfo.comment = "Unknown App"
        handle_transfer_transactions(wallet_address, group, exporter, txinfo)
