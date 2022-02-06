import logging
import urllib.parse
from datetime import datetime

from common.ErrorCounter import ErrorCounter
from common.TxInfo import TxInfo
from iotex import constants as co
from iotex.config_iotex import localconfig
from iotex.handle_transfer import (
    handle_staking_reward_transaction,
    handle_transfer_transaction,
    is_staking_reward_transaction,
    is_transfer_transaction,
)
from iotex.handle_unknown import handle_unknown


def process_txs(wallet_address, elems, exporter, progress):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)

        if i % 50 == 0:
            progress.report(i + 1, "Processed {} of {} transactions".format(i + 1, len(elems)))


def process_tx(wallet_address, elem, exporter):
    txid = elem["actHash"]
    txinfo = _txinfo(wallet_address, elem)

    try:
        if is_transfer_transaction(elem):
            handle_transfer_transaction(wallet_address, elem, exporter, txinfo)
        elif is_staking_reward_transaction(elem):
            handle_staking_reward_transaction(elem, exporter, txinfo)
        else:
            handle_unknown(exporter, txinfo)

    except Exception as e:
        logging.error("Exception when handling txid=%s, exception=%s", txid, str(e))
        ErrorCounter.increment("exception", txid)
        handle_unknown(exporter, txinfo)

        if localconfig.debug:
            raise(e)


def _txinfo(wallet_address, elem):
    txid = elem["actHash"]

    timestamp = datetime.utcfromtimestamp(elem["timestamp"]["seconds"]).strftime('%Y-%m-%d %H:%M:%S')

    url = "https://iotexscan.io/tx/{}".format(urllib.parse.quote(txid))
    txinfo = TxInfo(txid, timestamp, 0, co.CURRENCY_IOTEX, wallet_address, co.EXCHANGE_IOTEX_BLOCKCHAIN, url)

    return txinfo
