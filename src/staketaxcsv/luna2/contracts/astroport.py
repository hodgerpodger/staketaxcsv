import staketaxcsv.common.make_tx
import staketaxcsv.luna2.util_luna2
from staketaxcsv.luna2.contracts.config import CONTRACTS

CONTRACT_ASTROPORT_ROUTER = "terra1j8hayvehh3yy02c2vtw5fdhz9f4drhtee8p5n5rguvg3nyd6m83qd2y90a"
CONTRACT_ASTROPORT_ASTRO = "terra1nsuqsk6kh58ulczatwev87ttq2z6r3pusulg9r24mfj2fvtzd4uq3exn26"
CONTRACT_ASTROPORT_AIRDROP_REGISTRY = "terra15hlvnufpk8a3gcex09djzkhkz3jg9dpqvv6fvgd0ynudtu2z0qlq2fyfaq"
CONTRACT_ASTROPORT_LUNAAXLUSDCPAIR = "terra1fd68ah02gr2y8ze7tm9te7m70zlmc7vjyyhs6xlhsdmqqcjud4dql4wpxr"
CONTRACT_ASTROPORT_GENERATOR = "terra1ksvlfex49desf4c452j6dewdjs6c48nafemetuwjyj6yexd7x3wqvwa7j9"
CONTRACT_ASTROPORT_ROUTER_2 = "terra19hz374h6ruwtzrnm8ytkae782uv79h9yt9tuytgvt94t26c4793qnfg7vn"


def is_astroport_pair_contract(contract_data):
    return ("contract_info" in contract_data
           and contract_data["contract_info"].get("label") in ("Astroport pair", "Astroport LP token"))


def handle_astroport(elem, txinfo):
    rows = []

    for msginfo in txinfo.msgs:
        actions = msginfo.wasm

        if _is_swap(actions):
            result = _handle_swap(txinfo, msginfo)
        elif _is_xastro_staking(actions):
            result = _handle_xastro_staking(txinfo, msginfo)
        elif _is_airdrop(actions):
            result = _handle_airdrop(txinfo, msginfo)
        elif _is_airdrop_vesting_account(actions):
            result = _handle_aidrop_vesting_account(txinfo, msginfo)
        elif _is_increase_allowance(actions):
            result = _handle_increase_allowance(txinfo, msginfo)
        elif _is_provide_liquidity(actions):
            result = _handle_provide_liquidity(txinfo, msginfo)
        elif _is_withdraw_liquidity(actions):
            result = _handle_withdraw_liquidity(txinfo, msginfo)
        else:
            raise Exception("handle_astroport(): Unknown message.  actions={}".format(
                [action["action"] for action in actions]))

        rows.extend(result)
    return rows


def _is_provide_liquidity(actions):
    # example action lists:
    # ["provide_liquidity", "mint", "send", "deposit"]
    # ["provide_liquidity", "transfer_from", "mint", "send", "deposit"]
    # ["provide_liquidity", "transfer_from", "mint"]

    action_names = set([action["action"] for action in actions])
    pl_action_set = set(["provide_liquidity", "mint"])

    return pl_action_set.issubset(action_names)


def _handle_provide_liquidity(txinfo, msginfo):
    actions = msginfo.wasm

    pl_action = [action for action in actions if action["action"] == "provide_liquidity"][0]
    mint_action = [action for action in actions if action["action"] == "mint"][0]

    # Determine sent amounts
    sent_amounts = staketaxcsv.luna2.util_luna2.amount_assets_to_currency(pl_action["assets"])
    sent_amount_1, sent_currency_1 = sent_amounts[0]
    sent_amount_2, sent_currency_2 = sent_amounts[1]

    # Determine received LP currency
    lp_amount_raw = mint_action["amount"]
    lp_asset = mint_action["_contract_address"]
    lp_amount, lp_currency = staketaxcsv.luna2.util_luna2.lp_asset_to_currency(lp_amount_raw, lp_asset)

    # Create CSV rows
    rows = [
        staketaxcsv.common.make_tx.make_lp_deposit_tx(txinfo, sent_amount_1, sent_currency_1, lp_amount / 2, lp_currency),
        staketaxcsv.common.make_tx.make_lp_deposit_tx(txinfo, sent_amount_2, sent_currency_2, lp_amount / 2, lp_currency)
    ]

    return rows

def _is_withdraw_liquidity(actions):
    # example action lists:
    # ["send", "withdraw_liquidity", "burn"]

    action_names = [action["action"] for action in actions]

    if action_names == ["send", "withdraw_liquidity", "burn"]:
        return True
    else:
        return False


def _handle_withdraw_liquidity(txinfo, msginfo):
    actions = msginfo.wasm

    wl_action = [action for action in actions if action["action"] == "withdraw_liquidity"][0]

    # Determine received amounts
    rec_amounts = staketaxcsv.luna2.util_luna2.amount_assets_to_currency(wl_action["refund_assets"])
    rec_amount_1, rec_currency_1 = rec_amounts[0]
    rec_amount_2, rec_currency_2 = rec_amounts[1]

    # Determine received LP currency
    lp_amount_raw = wl_action["withdrawn_share"]
    lp_asset = wl_action["_contract_address"]
    lp_amount, lp_currency = staketaxcsv.luna2.util_luna2.lp_asset_to_currency(lp_amount_raw, lp_asset)

    # Create CSV rows
    rows = [
        staketaxcsv.common.make_tx.make_lp_withdraw_tx(txinfo, rec_amount_1, rec_currency_1, lp_amount / 2, lp_currency),
        staketaxcsv.common.make_tx.make_lp_withdraw_tx(txinfo, rec_amount_2, rec_currency_2, lp_amount / 2, lp_currency)
    ]

    return rows


def _is_swap(actions):
    # This is a swap transaction if all actions are only "swap" or "transfer"
    action_names = set([action["action"] for action in actions])
    return action_names == set(["swap", "transfer"]) or action_names == set(["swap"])


def _handle_swap(txinfo, msginfo):
    actions = msginfo.wasm
    swap_actions = [action for action in actions if action["action"] == "swap"]

    sent_amount_raw, sent_asset = swap_actions[0]["offer_amount"], swap_actions[0]["offer_asset"]
    received_amount_raw, received_asset = swap_actions[-1]["return_amount"], swap_actions[-1]["ask_asset"]

    sent_amount, sent_currency = staketaxcsv.luna2.util_luna2.asset_to_currency(sent_amount_raw, sent_asset)
    received_amount, received_currency = staketaxcsv.luna2.util_luna2.asset_to_currency(received_amount_raw, received_asset)

    row = staketaxcsv.common.make_tx.make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    return [row]


def _is_xastro_staking(actions):
    if (len(actions) == 2
         and actions[0]["action"] == "send"
         and actions[1]["action"] == "mint"):
        return True
    else:
        return False


def _handle_xastro_staking(txinfo, msginfo):
    actions = msginfo.wasm

    sent_amount_raw, sent_asset = actions[0]["amount"], actions[0]["_contract_address"]
    received_amount_raw, received_asset = actions[1]["amount"], actions[1]["_contract_address"]

    sent_amount, sent_currency = staketaxcsv.luna2.util_luna2.asset_to_currency(sent_amount_raw, sent_asset)
    received_amount, received_currency = staketaxcsv.luna2.util_luna2.asset_to_currency(received_amount_raw, received_asset)

    row = staketaxcsv.common.make_tx.make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    return [row]


def _is_airdrop(actions):
    if (len(actions) == 2
          and actions[0]["action"] == "Airdrop::ExecuteMsg::Claim"
          and actions[1]["action"] == "transfer"):
        return True
    else:
        return False


def _handle_airdrop(txinfo, msginfo):
    actions = msginfo.wasm

    reward_amount_raw, reward_asset = actions[1]["amount"], actions[1]["_contract_address"]
    reward_amount, reward_currency = staketaxcsv.luna2.util_luna2.asset_to_currency(reward_amount_raw, reward_asset)

    row = staketaxcsv.common.make_tx.make_airdrop_tx(txinfo, reward_amount, reward_currency)
    return [row]


def _is_airdrop_vesting_account(actions):
    if (len(actions) == 3
          and actions[0]["action"] == "withdraw"
          and actions[1]["action"] == "claim"
          and actions[2]["action"] == "transfer"):
        return True
    else:
        return False


def _handle_aidrop_vesting_account(txinfo, msginfo):
    actions = msginfo.wasm

    reward_amount_raw, reward_asset = actions[2]["amount"], actions[2]["_contract_address"]
    reward_amount, reward_currency = staketaxcsv.luna2.util_luna2.asset_to_currency(reward_amount_raw, reward_asset)

    row = staketaxcsv.common.make_tx.make_airdrop_tx(txinfo, reward_amount, reward_currency)
    return [row]


def _is_increase_allowance(actions):
    return len(actions) == 1 and actions[0]["action"] == "increase_allowance"


def _handle_increase_allowance(txinfo, msginfo):
    return []


# Astroport Swap
CONTRACTS[CONTRACT_ASTROPORT_ROUTER] = handle_astroport
CONTRACTS[CONTRACT_ASTROPORT_ROUTER_2] = handle_astroport

# Astroport Staking (xAstro)
CONTRACTS[CONTRACT_ASTROPORT_ASTRO] = handle_astroport

# Astroport Airdrop
CONTRACTS[CONTRACT_ASTROPORT_AIRDROP_REGISTRY] = handle_astroport
CONTRACTS[CONTRACT_ASTROPORT_GENERATOR] = handle_astroport
