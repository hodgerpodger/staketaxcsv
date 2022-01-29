import logging
import urllib.parse
from datetime import datetime

from algo import constants as co
from algo.asset import Algo
from algo.config_algo import localconfig
from algo.handle_tinyman import handle_tinyman_transaction, is_tinyman_transaction
from algo.handle_transfer import (
    handle_asa_transaction,
    handle_governance_reward_transaction,
    handle_payment_transaction,
    is_governance_reward_transaction,
)
from algo.handle_unknown import handle_unknown
from algo.handle_yieldly import handle_yieldly_transaction, is_yieldly_transaction
from common.ErrorCounter import ErrorCounter
from common.TxInfo import TxInfo


def process_txs(wallet_address, elems, exporter, progress):
    length = len(elems)
    i = 0
    while i < length:
        elem = elems[i]
        txid = elem["id"]

        try:
            groupid = elem.get("group", None)
            if not groupid:
                txinfo = _txinfo(wallet_address, elem)
                txtype = elem["tx-type"]
                if txtype == co.TRANSACTION_TYPE_PAYMENT:
                    handle_payment_transaction(wallet_address, elem, exporter, txinfo)
                elif txtype == co.TRANSACTION_TYPE_ASSET_TRANSFER:
                    handle_asa_transaction(wallet_address, elem, exporter, txinfo)
                else:
                    handle_unknown(exporter, txinfo)
            else:
                txinfo = _grouptxinfo(wallet_address, elem)
                group = _get_transaction_group(groupid, i, elems)
                _handle_transaction_group(wallet_address, group, exporter, txinfo)
                i += len(group) - 1
        except Exception as e:
            logging.error("Exception when handling txid=%s, exception=%s", txid, str(e))
            ErrorCounter.increment("exception", txid)
            handle_unknown(exporter, txinfo)

            if localconfig.debug:
                raise(e)

        if i % 50 == 0:
            progress.report(i + 1, "Processed {} of {} transactions".format(i + 1, length))
        i += 1


def _txinfo(wallet_address, elem):
    txid = elem["id"]
    txsender = elem["sender"]

    timestamp = datetime.utcfromtimestamp(elem["round-time"]).strftime('%Y-%m-%d %H:%M:%S')
    fee = Algo(elem["fee"] if txsender == wallet_address else 0)

    url = "https://algoexplorer.io/tx/{}".format(urllib.parse.quote(txid))
    txinfo = TxInfo(txid, timestamp, fee, fee.ticker, wallet_address, co.EXCHANGE_ALGORAND_BLOCKCHAIN, url)

    return txinfo


def _grouptxinfo(wallet_address, elem):
    groupid = elem["group"]
    txid = groupid
    timestamp = datetime.utcfromtimestamp(elem["round-time"]).strftime('%Y-%m-%d %H:%M:%S')
    fee = Algo(0)
    url = "https://algoexplorer.io/tx/group/{}".format(urllib.parse.quote(groupid))
    txinfo = TxInfo(txid, timestamp, fee, fee.ticker, wallet_address, co.EXCHANGE_ALGORAND_BLOCKCHAIN, url)

    return txinfo


def _get_transaction_group(groupid, i, elems):
    group = []
    length = len(elems)
    while i < length:
        elem = elems[i]
        current_groupid = elem.get("group", None)
        if current_groupid != groupid:
            break
        group.append(elem)
        i += 1
    # Make sure the transactions are in the right order
    return sorted(group, key=lambda val: val["intra-round-offset"])


def _handle_transaction_group(wallet_address, group, exporter, txinfo):
    # TODO handle algofi and algomint transactions
    if is_governance_reward_transaction(wallet_address, group):
        handle_governance_reward_transaction(group, exporter, txinfo)
    elif is_tinyman_transaction(group):
        handle_tinyman_transaction(group, exporter, txinfo)
    elif is_yieldly_transaction(group):
        handle_yieldly_transaction(group, exporter, txinfo)
    else:
        handle_unknown(exporter, txinfo)
