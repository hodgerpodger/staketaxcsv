import common.make_tx
from luna2.contracts.config import CONTRACTS
import luna2.util_luna2

CONTRACT_ASTROPORT_ROUTER = "terra1j8hayvehh3yy02c2vtw5fdhz9f4drhtee8p5n5rguvg3nyd6m83qd2y90a"
CONTRACT_ASTROPORT_ASTRO = "terra1nsuqsk6kh58ulczatwev87ttq2z6r3pusulg9r24mfj2fvtzd4uq3exn26"
CONTRACT_ASTROPORT_AIRDROP_REGISTRY = "terra15hlvnufpk8a3gcex09djzkhkz3jg9dpqvv6fvgd0ynudtu2z0qlq2fyfaq"


def handle_astroport_swap(elem, txinfo):
    actions = txinfo.msgs[0].wasm
    swap_actions = [action for action in actions if action["action"] == "swap"]

    assert(len(swap_actions) > 0)

    sent_amount_raw, sent_asset = swap_actions[0]["offer_amount"], swap_actions[0]["offer_asset"]
    received_amount_raw, received_asset = swap_actions[-1]["return_amount"], swap_actions[-1]["ask_asset"]

    sent_amount, sent_currency = luna2.util_luna2.asset_to_currency(sent_amount_raw, sent_asset)
    received_amount, received_currency = luna2.util_luna2.asset_to_currency(received_amount_raw, received_asset)

    row = common.make_tx.make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    return [row]


def handle_xastro_staking(elem, txinfo):
    actions = txinfo.msgs[0].wasm

    assert(len(txinfo.msgs) == 1)
    assert(len(actions) == 2)
    assert(actions[0]["action"] == "send")
    assert(actions[1]["action"] == "mint")

    sent_amount_raw, sent_asset = actions[0]["amount"], actions[0]["_contract_address"]
    received_amount_raw, received_asset = actions[1]["amount"], actions[1]["_contract_address"]

    sent_amount, sent_currency = luna2.util_luna2.asset_to_currency(sent_amount_raw, sent_asset)
    received_amount, received_currency = luna2.util_luna2.asset_to_currency(received_amount_raw, received_asset)

    row = common.make_tx.make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    return [row]


def handle_astroport_airdrop(elem, txinfo):
    actions = txinfo.msgs[0].wasm

    assert(len(txinfo.msgs) == 1)
    assert(actions[0]["action"] == "Airdrop::ExecuteMsg::Claim")
    assert(actions[1]["action"] == "transfer")

    reward_amount_raw, reward_asset = actions[1]["amount"], actions[1]["_contract_address"]
    reward_amount, reward_currency = luna2.util_luna2.asset_to_currency(reward_amount_raw, reward_asset)

    row = common.make_tx.make_airdrop_tx(txinfo, reward_amount, reward_currency)
    return [row]


# Astroport Swap
CONTRACTS[CONTRACT_ASTROPORT_ROUTER] = handle_astroport_swap

# Astrport Staking (xAstro)
CONTRACTS[CONTRACT_ASTROPORT_ASTRO] = handle_xastro_staking

# Astroport Airdrop
CONTRACTS[CONTRACT_ASTROPORT_AIRDROP_REGISTRY] = handle_astroport_airdrop
