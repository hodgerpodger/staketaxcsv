import logging

from staketaxcsv.algo.config_algo import localconfig
from staketaxcsv.algo.export_tx import export_unknown
from staketaxcsv.algo.handle_group import get_group_txinfo, get_transaction_group, handle_transaction_group
from staketaxcsv.algo.transaction import get_transaction_txinfo
from staketaxcsv.common.ErrorCounter import ErrorCounter


def process_txs(wallet_address, transactions, exporter, progress):
    length = len(transactions)
    i = 0
    while i < length:
        transaction = transactions[i]
        txid = transaction["id"]

        try:
            groupid = transaction.get("group")
            if not groupid:
                txinfo = get_transaction_txinfo(wallet_address, transaction)
                group = [transaction]
            else:
                txinfo = get_group_txinfo(wallet_address, transaction)
                group = get_transaction_group(groupid, i, transactions)
            handle_transaction_group(wallet_address, group, exporter, txinfo)
            i += len(group) - 1
        except Exception as e:
            logging.error("Exception when handling txid=%s, exception=%s", txid, str(e))
            ErrorCounter.increment("exception", txid)
            export_unknown(exporter, txinfo)

            if localconfig.debug:
                raise (e)

        if i % 50 == 0:
            progress.report(i + 1, "Processed {} of {} transactions".format(i + 1, length))
        i += 1
