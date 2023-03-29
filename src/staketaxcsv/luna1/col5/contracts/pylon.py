
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.luna1.make_tx import make_swap_tx_terra, make_gov_stake_tx, make_gov_unstake_tx
from staketaxcsv.common.make_tx import make_income_tx, make_simple_tx


def handle_pylon(elem, txinfo):
    txid = txinfo.txid
    msgs = txinfo.msgs
    contract = util_terra._contract(elem, 0)

    if contract == STAKING_CONTRACT:
        if _is_pool_withdraw(msgs):
            return _handle_staking_withdraw(elem, txinfo, msgs)
    elif _is_pool_deposit(msgs):
        return _handle_pool_deposit(elem, txinfo, msgs)
    elif _is_pool_withdraw(msgs):
        return _handle_pool_withdraw(elem, txinfo, msgs)
    elif contract in [ANCHOR_REWARDS_CONTRACT, VALKYRIE_REWARDS_CONTRACT]:
        return _handle_rewards_claim(elem, txinfo, msgs)
    else:
        return make_simple_tx(txinfo, "PYLON_UNKNOWN")

    raise Exception("handle_pylon(): Unable to handle txid={}".format(txid))


def _is_pool_deposit(msgs):
    if "deposit" in msgs[0].execute_msg:
        return True

def _is_pool_withdraw(msgs):
    if "withdraw" in msgs[0].execute_msg:
        return True

def _handle_rewards_claim(elem, txinfo, msgs):
    txinfo.comment = "Pylon MINE claim"
    transfers_in, _ = util_terra._transfers_from_actions(msgs[0], txinfo.wallet_address, txinfo.txid)

    if(len(transfers_in) == 1):
        receive_currency = util_terra._asset_to_currency(transfers_in[0][1], txinfo.txid)
        receive_amount = util_terra._float_amount(transfers_in[0][0], receive_currency)
        return [make_income_tx(txinfo, receive_amount, receive_currency, txinfo.txid)]

def _handle_staking_withdraw(elem, txinfo, msgs):
    txid = txinfo.txid
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]

    receive_currency = util_terra._asset_to_currency(from_contract["contract_address"][1], txid)
    receive_amount = util_terra._float_amount(from_contract["amount"][1], receive_currency)

    row = make_gov_unstake_tx(txinfo, receive_amount, receive_currency)
    return [row]


def _handle_pool_deposit(elem, txinfo, msgs):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    mint_action = msgs[0].actions[-1]
    assert(mint_action['action'] == "mint")

    _, transfers_out = util_terra._transfers(elem, wallet_address, txid)

    sent_currency = transfers_out[0][1]
    sent_amount = transfers_out[0][0]
    receive_currency = util_terra._asset_to_currency(mint_action["contract_address"], txid)
    receive_amount = util_terra._float_amount(mint_action["amount"], receive_currency)

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, receive_amount, receive_currency)
    return [row]


def _handle_pool_withdraw(elem, txinfo, msgs):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    burn_action = msgs[1].actions[0]
    assert(burn_action['action'] == "send")

    transfers_in, _ = util_terra._transfers(elem, wallet_address, txid)

    sent_currency = util_terra._asset_to_currency(burn_action["contract_address"], txid)
    sent_amount = util_terra._float_amount(burn_action["amount"], sent_currency)
    receive_currency = transfers_in[0][1]
    receive_amount = transfers_in[0][0]

    row = make_swap_tx_terra(txinfo, sent_amount, sent_currency, receive_amount, receive_currency)
    return [row]

VALKYRIE_REWARDS_CONTRACT = "terra1p625agkeu4vrr4fqnl5c82myhy3z95t6tqycku"
ANCHOR_REWARDS_CONTRACT = "terra19vnwdqz4um0z8f69pc8y0z4ncrcxm4cjf3gevz"
STAKING_CONTRACT = "terra19nek85kaqrvzlxygw20jhy08h3ryjf5kg4ep3l"
CONTRACTS["terra1jk0xh49ft2ls4u9dlfqweed8080u6ysumvmtcz"] = handle_pylon
CONTRACTS["terra10jrv8wy6s06mku9t6yawt2yr09wjlqsw0qk0vf"] = handle_pylon
CONTRACTS[STAKING_CONTRACT] = handle_pylon
CONTRACTS[ANCHOR_REWARDS_CONTRACT] = handle_pylon
CONTRACTS[VALKYRIE_REWARDS_CONTRACT] = handle_pylon
