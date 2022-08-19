import common.ibc.handle
import common.make_tx
from luna2.contracts.config import CONTRACTS
import luna2.util_luna2

CONTRACT_VALKYRIE_AIRDROP = "terra10dxw3jhvu48dj2nnh6urq706gqwqapsa5rzmyynrep82xhnefvdq4hwn3j"


def handle_airdrop(elem, txinfo):
    rows = []

    for msginfo in txinfo.msgs:
        actions = msginfo.wasm

        if len(actions) == 2 and actions[0]["action"] == "claim" and actions[1]["action"] == "transfer":
            reward_amount_raw = actions[1]["amount"]
            reward_asset = actions[1]["_contract_address"]
            reward_amount, reward_currency = luna2.util_luna2.asset_to_currency(reward_amount_raw, reward_asset)
            row = common.make_tx.make_airdrop_tx(txinfo, reward_amount, reward_currency)
            rows.append(row)
        elif len(actions) == 1 and actions[0]["action"] == "claim":
            continue
        else:
            rows.extend(common.ibc.handle.unknown_txs_detect_transfers(txinfo, msginfo))

    return rows


CONTRACTS[CONTRACT_VALKYRIE_AIRDROP] = handle_airdrop
