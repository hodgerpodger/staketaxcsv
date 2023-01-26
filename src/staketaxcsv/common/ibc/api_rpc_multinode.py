import staketaxcsv.common.ibc.api_rpc
from staketaxcsv.common.ibc.api_common import remove_duplicates


def get_tx(nodes, txid):
    elem = None
    for node in nodes:
        elem = staketaxcsv.common.ibc.api_rpc.get_tx(node, txid)
        if elem:
            break
    return elem


def get_txs_pages_count(nodes, wallet_address, max_txs):
    pages_total = 0
    for node in nodes:
        pages_total += staketaxcsv.common.ibc.api_rpc.get_txs_pages_count(node, wallet_address, max_txs)
    return pages_total


def get_txs_all(nodes, wallet_address, progress, max_txs):
    elems = []
    for node in nodes:
        elems.extend(staketaxcsv.common.ibc.api_rpc.get_txs_all(node, wallet_address, progress, max_txs))
    elems = remove_duplicates(elems)
    return elems
