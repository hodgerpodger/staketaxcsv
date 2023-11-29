from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.common.make_tx import make_transfer_in_tx, make_transfer_out_tx, make_simple_tx

PRISM_FORGE_CONTRACT = "terra1angxk38zehp0k09m0wqrrxf0r3ces6qjj432l8"


def handle_prism_withdraw(elem, txinfo):
    txid = txinfo.txid
    txinfo.comment += "Prism withdraw"
    rows = []

    transfers_in, transfers_out = util_terra._transfers(elem, txinfo.wallet_address, txid)

    for transfer in transfers_in:
        rows.append(make_transfer_in_tx(txinfo, transfer[0], transfer[1], txid))

    for transfer in transfers_out:
        rows.append(make_transfer_out_tx(txinfo, transfer[0], transfer[1], txid))

    if len(rows) == 0:
        return [make_simple_tx(txinfo, "PRISM_UNKNOWN")]
    else:
        return rows


CONTRACTS[PRISM_FORGE_CONTRACT] = handle_prism_withdraw
