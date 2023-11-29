
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.common.make_tx import make_transfer_in_tx, make_transfer_out_tx
from staketaxcsv.common.ExporterTypes import (
    TX_TYPE_MARS_UNKNOWN,
    TX_TYPE_TRANSFER
)

TERRANADO_CONTRACT = "terra1tzhh2yt0arrwttpywg65vy0kyu99n22jhjxva7"


def handle_terranado_deposit(elem, txinfo):
    txid = txinfo.txid
    txinfo.comment += "Terranado deposit"
    rows = []

    transfers_in, transfers_out = util_terra._transfers(elem, txinfo.wallet_address, txid)

    for transfer in transfers_in:
        rows.append(make_transfer_in_tx(txinfo, transfer[0], transfer[1], txid))

    for transfer in transfers_out:
        rows.append(make_transfer_out_tx(txinfo, transfer[0], transfer[1], txid))

    return rows


CONTRACTS[TERRANADO_CONTRACT] = handle_terranado_deposit
