
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col5.contracts.config import CONTRACTS
from staketaxcsv.luna1.make_tx import make_swap_tx_terra


def _extract_asset_info_contract_or_denom(asset_info):
    if 'native_token' in asset_info:
        return asset_info['native_token']['denom']

    return asset_info['token']['contract_addr']


def handle_terraswap_route_swap(elem, txinfo):

    txid = txinfo.txid
    COMMENT = "terraswap route swap"

    for msg in txinfo.msgs:
        execute_swap_operations = msg.execute_msg['execute_swap_operations']

        offer_amount = execute_swap_operations['offer_amount']
        offer_asset_info = execute_swap_operations['operations'][0]
        offer_currency = util_terra._asset_to_currency(_extract_asset_info_contract_or_denom(offer_asset_info['terra_swap']['offer_asset_info']), txid)
        receive_info = execute_swap_operations['operations'][-1]
        receive_amount = util_terra._event_from_log(elem, 'from_contract')['return_amount'][-1]
        receive_currency = util_terra._asset_to_currency(_extract_asset_info_contract_or_denom(receive_info['terra_swap']['ask_asset_info']), txid)
        row = make_swap_tx_terra(
            txinfo,
            util_terra._float_amount(offer_amount, offer_currency),
            offer_currency,
            util_terra._float_amount(receive_amount, receive_currency),
            receive_currency,
            txid=txid,
            empty_fee=False
        )
        row.comment = COMMENT

        return [row]


# Terraswap Route Swap
CONTRACTS["terra19qx5xe6q9ll4w0890ux7lv2p4mf3csd4qvt3ex"] = handle_terraswap_route_swap
