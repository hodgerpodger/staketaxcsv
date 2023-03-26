
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.common.make_tx import make_simple_tx
from staketaxcsv.common.ExporterTypes import (
    TX_TYPE_MARS_UNKNOWN,
    TX_TYPE_TRANSFER
)

EDGE_CONTRACT = "terra13zggcrrf5cytnsmv33uwrtf56c258vqrhckkj6"

def handle_edge_repay(elem, txinfo):
    txid = txinfo.txid
    txinfo.comment = "EDGE repay"
    rows = []

    rows.append(make_simple_tx(txinfo, "EDGE_UNKNOWN"))

    return rows


CONTRACTS[EDGE_CONTRACT] = handle_edge_repay