import staketaxcsv.common.ibc.api_rpc
from staketaxcsv.common.ibc.util_ibc import remove_duplicates
from staketaxcsv.common.ibc.api_rpc import TXS_LIMIT_PER_QUERY


def get_tx(nodes, txid):
    elem = None
    for node in nodes:
        elem = staketaxcsv.common.ibc.api_rpc.get_tx(node, txid)
        if elem:
            break
    return elem


def get_txs_pages_count(nodes, wallet_address, max_txs, progress_rpc=None, limit=TXS_LIMIT_PER_QUERY):
    pages_total = 0
    txs_total = 0
    for node in nodes:
        num_pages, num_txs = staketaxcsv.common.ibc.api_rpc.get_txs_pages_count(node, wallet_address, max_txs, limit)
        pages_total += num_pages
        txs_total += num_txs

        if progress_rpc:
            progress_rpc.set_estimate_node(node, num_pages, num_txs)

    return pages_total, txs_total


def get_txs_all(nodes, wallet_address, max_txs, progress_rpc=None, limit=TXS_LIMIT_PER_QUERY):
    elems = []
    for node in nodes:
        stage_name_fetch = node + "_fetch"
        stage_name_normalize = node + "_normalize"

        # fetch
        cur_elems = staketaxcsv.common.ibc.api_rpc.get_txs_all(
            node, wallet_address, max_txs, progress=progress_rpc, limit=limit, stage_name=stage_name_fetch)

        if progress_rpc:
            progress_rpc.update_estimate_node(node, len(cur_elems))

        # normalize data into lcd data processor
        staketaxcsv.common.ibc.api_rpc.normalize_rpc_txns(
            node, cur_elems, progress_rpc, stage_name=stage_name_normalize)

        elems.extend(cur_elems)

    elems = remove_duplicates(elems)
    return elems
