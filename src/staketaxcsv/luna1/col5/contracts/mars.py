
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.luna1.make_tx import _make_tx_received, _make_tx_sent
from staketaxcsv.common.ExporterTypes import (
    TX_TYPE_MARS_UNKNOWN,
    TX_TYPE_TRANSFER
)

MARS_FIELD_LUNA_UST_CONTRACT = "terra1kztywx50wv38r58unxj9p6k3pgr2ux6w5x68md"
MARS_FIELD_ANC_UST_CONTRACT = "terra1vapq79y9cqghqny7zt72g4qukndz282uvqwtz6"
MARS_FIELD_MIR_UST_CONTRACT = "terra12dq4wmfcsnz6ycep6ek4umtuaj6luhfp256hyu"

def handle_mars_unbond(elem, txinfo):
    txid = txinfo.txid
    txinfo.comment = "MARS unbond"
    rows = []

    transfers_in, transfers_out = util_terra._transfers(elem, txinfo.wallet_address, txid)

    for amount, currency in transfers_in:
        rows.append(_make_tx_received(txinfo, amount, currency, TX_TYPE_TRANSFER, txid))

    for amount, currency in transfers_out:
        rows.append(_make_tx_sent(txinfo, amount, currency, TX_TYPE_TRANSFER, txid))
    
    return rows


CONTRACTS[MARS_FIELD_LUNA_UST_CONTRACT] = handle_mars_unbond
CONTRACTS[MARS_FIELD_ANC_UST_CONTRACT] = handle_mars_unbond
CONTRACTS[MARS_FIELD_MIR_UST_CONTRACT] = handle_mars_unbond