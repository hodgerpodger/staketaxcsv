from staketaxcsv.common.make_tx import make_airdrop_tx, make_swap_tx
from staketaxcsv.luna1 import constants as co
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.luna1.constants import CUR_ASTRO

CONTRACT_ASTROPORT_AIRDROP = "terra1dpe2aqykm2vnakcz4vgpha0agxnlkjvgfahhk7"

CURRENCY_ADDRESS_ASTRO = "terra1xj49zyqrwpv5k928jwfpfy2ha668nwdgkwlrg3"
CURRENCY_ADDRESS_XASTRO = "terra14lpnyzc9z4g3ugr4lhm8s4nle0tq8vcltkhzh7"


def handle_astroport_airdrop(elem, txinfo):
    txid = txinfo.txid

    for msg in txinfo.msgs:
        contract = msg.contract

        if contract == CONTRACT_ASTROPORT_AIRDROP:
            for action in msg.actions:
                if action["action"] == "Airdrop::ExecuteMsg::Claim":
                    amount_string = action["airdrop"]
                    currency = CUR_ASTRO
                    amount = util_terra._float_amount(amount_string, currency)

                    row = make_airdrop_tx(txinfo, amount, currency)
                    return [row]

    raise Exception("handle_astroport_airdrop(): Unable to handle txid={}".format(txid))


def handle_astro(elem, txinfo):
    txid = txinfo.txid
    msgs = txinfo.msgs

    if _is_astro_stake(msgs):
        return _handle_astro_stake(elem, txinfo, msgs)
    elif _is_astroport_swap(msgs):
        return _handle_astroport_swap(elem, txinfo, msgs)

    raise Exception("handle_astroport(): Unable to handle txid={}".format(txid))


def _is_astro_stake(msgs):
    if len(msgs) == 1:
        actions = msgs[0].actions
        if len(actions) == 2:
            if actions[0]["action"] == "send" and actions[1]["action"] == "mint":
                if (actions[0]["contract_address"] == CURRENCY_ADDRESS_ASTRO
                   and actions[1]["contract_address"] == CURRENCY_ADDRESS_XASTRO):
                    return True
    return False


def _is_astroport_swap(msgs):
    if len(msgs) == 1:
        actions = msgs[0].actions
        if len(actions) == 2:
            if actions[0]["action"] == "send" and actions[1]["action"] == "swap":
                return True
    return False


def _handle_astroport_swap(elem, txinfo, msgs):
    txid = txinfo.txid
    send_action, swap_action = msgs[0].actions[0], msgs[0].actions[1]
    assert(send_action["action"] == "send")
    assert(swap_action["action"] == "swap")

    sent_currency = util_terra._asset_to_currency(swap_action["offer_asset"], txid)
    sent_amount = util_terra._float_amount(send_action["amount"], sent_currency)
    receive_currency = util_terra._asset_to_currency(swap_action["ask_asset"], txid)
    receive_amount = util_terra._float_amount(swap_action["return_amount"], receive_currency)

    row = make_swap_tx(txinfo, sent_amount, sent_currency, receive_amount, receive_currency)
    return [row]


def handle_xastro(elem, txinfo):
    txid = txinfo.txid
    msgs = txinfo.msgs

    if _is_astro_unstake(msgs):
        return _handle_astro_unstake(elem, txinfo, msgs)

    raise Exception("handle_astroport(): Unable to handle txid={}".format(txid))


def _handle_astro_stake(elem, txinfo, msgs):
    txid = txinfo.txid
    actions = msgs[0].actions
    send_action, mint_action = actions[0], actions[1]

    sent_currency = util_terra._lookup_address(send_action["contract_address"], txid)
    sent_amount = util_terra._float_amount(send_action["amount"], sent_currency)
    receive_currency = util_terra._lookup_address(mint_action["contract_address"], txid)
    receive_amount = util_terra._float_amount(mint_action["amount"], receive_currency)

    assert (send_action["action"] == "send")
    assert (mint_action["action"] == "mint")
    assert(receive_currency.upper() == co.CUR_XASTRO)
    assert(sent_currency.upper() == co.CUR_ASTRO)

    row = make_swap_tx(txinfo, sent_amount, sent_currency, receive_amount, receive_currency)
    return [row]


def _is_astro_unstake(msgs):
    if len(msgs) == 1:
        actions = msgs[0].actions
        if len(actions) == 3:
            if (actions[0]["action"] == "send"
                 and actions[1]["action"] == "burn"
                 and actions[2]["action"] == "transfer"):
                if actions[1]["contract_address"] == CURRENCY_ADDRESS_XASTRO:
                    return True
    return False


def _handle_astro_unstake(elem, txinfo, msgs):
    txid = txinfo.txid
    actions = msgs[0].actions
    send_action, burn_action, transfer_action = actions[0], actions[1], actions[2]

    sent_currency = util_terra._lookup_address(send_action["contract_address"], txid)
    sent_amount = util_terra._float_amount(send_action["amount"], sent_currency)
    receive_currency = util_terra._lookup_address(transfer_action["contract_address"], txid)
    receive_amount = util_terra._float_amount(transfer_action["amount"], receive_currency)

    assert (send_action["action"] == "send")
    assert (burn_action["action"] == "burn")
    assert (transfer_action["action"] == "transfer")
    assert (sent_currency.upper() == co.CUR_XASTRO)
    assert (receive_currency.upper() == co.CUR_ASTRO)

    row = make_swap_tx(txinfo, sent_amount, sent_currency, receive_amount, receive_currency)
    return [row]


# Astroport Rewards Airdrop
CONTRACTS[CONTRACT_ASTROPORT_AIRDROP] = handle_astroport_airdrop

# stake ASTRO, astroport swap
CONTRACTS[CURRENCY_ADDRESS_ASTRO] = handle_astro

# unstake ASTRO
CONTRACTS[CURRENCY_ADDRESS_XASTRO] = handle_xastro
