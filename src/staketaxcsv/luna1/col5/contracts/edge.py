
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.common.make_tx import make_swap_tx, make_repay_tx, make_borrow_tx, make_simple_tx

EDGE_CONTRACT = "terra13zggcrrf5cytnsmv33uwrtf56c258vqrhckkj6"


def handle_edge(elem, txinfo):
    execute_msg = util_terra._execute_msg(elem)

    if "increase_allowance" in execute_msg:
        execute_msg = util_terra._execute_msg(elem, 1)

    if "deposit" in execute_msg:
        return handle_edge_deposit(elem, txinfo)
    elif "borrow" in execute_msg:
        return handle_edge_borrow(elem, txinfo)
    elif "repay" in execute_msg:
        return handle_edge_repay(elem, txinfo)
    elif "withdraw" in execute_msg:
        return handle_edge_withdraw(elem, txinfo)
    else:
        return [make_simple_tx(txinfo, "EDGE_UNKNOWN")]


def handle_edge_deposit(elem, txinfo):
    txid = txinfo.txid
    msgs = txinfo.msgs
    txinfo.comment += "EDGE deposit"

    amount_received = ""
    currency_received = ""
    amount_sent = ""
    currency_sent = ""

    for action in msgs[0].actions:
        if action["action"] == "deposit":
            _, transfers_out = util_terra._transfers(elem, txinfo.wallet_address, txid)
            amount_sent, currency_sent = transfers_out[0]
        elif action["action"] == "mint":
            currency_contract = action["contract_address"]
            currency_received = util_terra._asset_to_currency(currency_contract, txid)
            amount_received = util_terra._float_amount(action["amount"], currency_received)
        else:
            return [make_simple_tx(txinfo, "EDGE_UNKNOWN")]

    return [make_swap_tx(txinfo, amount_sent, currency_sent, amount_received, currency_received, txid)]


def handle_edge_borrow(elem, txinfo):
    txid = txinfo.txid
    msgs = txinfo.msgs
    txinfo.comment += "EDGE borrow"

    for action in msgs[0].actions:
        if action["action"] == "borrow":
            currency_contract = action["underlying"]
            currency_received = util_terra._asset_to_currency(currency_contract, txid)
            amount_received = util_terra._float_amount(action["amount"], currency_received)
            return [make_borrow_tx(txinfo, amount_received, currency_received)]
        else:
            return [make_simple_tx(txinfo, "EDGE_UNKNOWN")]


def handle_edge_withdraw(elem, txinfo):
    txid = txinfo.txid
    msgs = txinfo.msgs
    txinfo.comment += "EDGE repay"

    amount_received = ""
    currency_received = ""
    amount_sent = ""
    currency_sent = ""

    for action in msgs[1].actions:
        if action["action"] == "withdraw":
            transfers_in, _ = util_terra._transfers(elem, txinfo.wallet_address, txid)
            amount_received, currency_received = transfers_in[0]
        elif action["action"] == "burn_from":
            currency_contract = action["contract_address"]
            currency_sent = util_terra._asset_to_currency(currency_contract, txid)
            amount_sent = util_terra._float_amount(action["amount"], currency_sent)
        else:
            return [make_simple_tx(txinfo, "EDGE_UNKNOWN")]

    return [make_swap_tx(txinfo, amount_sent, currency_sent, amount_received, currency_received, txid)]


def handle_edge_repay(elem, txinfo):
    txid = txinfo.txid
    msgs = txinfo.msgs
    txinfo.comment += "EDGE repay"

    for action in msgs[1].actions:
        if action["action"] == "repay":
            currency_contract = action["underlying"]
            currency_sent = util_terra._asset_to_currency(currency_contract, txid)
            amount_sent = util_terra._float_amount(action["amount"], currency_sent)
            return [make_repay_tx(txinfo, amount_sent, currency_sent)]
        else:
            return [make_simple_tx(txinfo, "EDGE_UNKNOWN")]


CONTRACTS[EDGE_CONTRACT] = handle_edge
