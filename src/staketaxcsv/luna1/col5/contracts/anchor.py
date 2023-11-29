
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.common.make_tx import make_transfer_in_tx, make_transfer_out_tx

LIQUIDATION_REMEDIATION_CONTRACT = "terra13v4ln23tmfs2zk4nh5dw5mzufckekp4fpafpcy"


def handle_remediation_claim(elem, txinfo):
    txid = txinfo.txid
    txinfo.comment += "Remediation claim"
    rows = []

    transfers_in, transfers_out = util_terra._transfers_from_actions(txinfo.msgs[0], txinfo.wallet_address, txid)

    for transfer in transfers_in:
        rows.append(make_transfer_in_tx(txinfo, transfer[0], transfer[1], txid))

    for transfer in transfers_out:
        rows.append(make_transfer_out_tx(txinfo, transfer[0], transfer[1], txid))

    return rows


CONTRACTS[LIQUIDATION_REMEDIATION_CONTRACT] = handle_remediation_claim
