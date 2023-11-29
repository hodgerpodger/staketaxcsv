
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.luna1.make_tx import _make_tx_received, _make_tx_sent, make_simple_tx
from staketaxcsv.common.make_tx import make_swap_tx
from staketaxcsv.common.ExporterTypes import (
    TX_TYPE_MARS_UNKNOWN,
    TX_TYPE_TRANSFER
)

MARS_FIELD_LUNA_UST_CONTRACT = "terra1kztywx50wv38r58unxj9p6k3pgr2ux6w5x68md"
MARS_FIELD_ANC_UST_CONTRACT = "terra1vapq79y9cqghqny7zt72g4qukndz282uvqwtz6"
MARS_FIELD_MIR_UST_CONTRACT = "terra12dq4wmfcsnz6ycep6ek4umtuaj6luhfp256hyu"
MARS_RED_BANK_CONTRACT = "terra19dtgj9j5j7kyf3pmejqv8vzfpxtejaypgzkz5u"


def handle_mars_unbond(elem, txinfo):
    txid = txinfo.txid
    txinfo.comment += "MARS unbond"
    rows = []

    transfers_in, transfers_out = util_terra._transfers(elem, txinfo.wallet_address, txid)

    for amount, currency in transfers_in:
        rows.append(_make_tx_received(txinfo, amount, currency, TX_TYPE_TRANSFER, txid))

    for amount, currency in transfers_out:
        rows.append(_make_tx_sent(txinfo, amount, currency, TX_TYPE_TRANSFER, txid))

    return rows


def handle_mars_deposit(elem, txinfo):
    txid = txinfo.txid
    msgs = txinfo.msgs
    txinfo.comment += "MARS deposit"

    amount_received = ""
    currency_received = ""
    amount_sent = ""
    currency_sent = ""

    for action in msgs[0].actions:
        if action["action"] == "deposit":
            _, transfers_out = util_terra._transfers(elem, txinfo.wallet_address, txid)
            amount_sent, currency_sent = transfers_out[0]
        elif action["action"] == "mint" and action["to"] == txinfo.wallet_address:
            currency_contract = action["contract_address"]
            currency_received = util_terra._asset_to_currency(currency_contract, txid)
            amount_received = util_terra._float_amount(action["amount"], currency_received)

    return [make_swap_tx(txinfo, amount_sent, currency_sent, amount_received, currency_received, txid)]


CONTRACTS[MARS_FIELD_LUNA_UST_CONTRACT] = handle_mars_unbond
CONTRACTS[MARS_FIELD_ANC_UST_CONTRACT] = handle_mars_unbond
CONTRACTS[MARS_FIELD_MIR_UST_CONTRACT] = handle_mars_unbond
CONTRACTS[MARS_RED_BANK_CONTRACT] = handle_mars_deposit
