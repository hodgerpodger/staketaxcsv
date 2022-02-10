from terra import util_terra
from terra.handle_lp import _handle_lp_deposit, _handle_lp_withdraw
from terra.make_tx import make_lp_stake_tx, make_lp_unstake_tx, make_swap_tx_terra


def handle_zap_into_strategy(exporter, elem, txinfo):
    comment = "apollo zap into strategy"
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]

    rows = []

    # swap row
    rows.extend(_handle_swap(txinfo, from_contract))

    # lp deposit collateral rows
    rows.extend(_handle_lp_deposit(txinfo, from_contract))

    # lp stake row
    rows.extend(_handle_lp_stake(txinfo, from_contract))

    util_terra._ingest_rows(exporter, rows, comment)


def handle_zap_out_of_strategy(exporter, elem, txinfo):
    comment = "apollo zap out of strategy"
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]

    rows = []

    # lp unstake row
    rows.extend(_handle_lp_unstake(txinfo, from_contract))

    # lp withdraw collateral rows
    rows.extend(_handle_lp_withdraw(elem, txinfo, from_contract))

    # swap row
    rows.extend(_handle_swap(txinfo, from_contract))

    util_terra._ingest_rows(exporter, rows, comment)


def _handle_swap(txinfo, from_contract):
    txid = txinfo.txid

    # Handle swap
    swap_sent_currency = util_terra._asset_to_currency(from_contract["offer_asset"][0], txid)
    swap_sent_amount = util_terra._float_amount(from_contract["offer_amount"][0], swap_sent_currency)
    swap_received_currency = util_terra._asset_to_currency(from_contract['ask_asset'][0], txid)
    swap_received_amount = util_terra._float_amount(from_contract["return_amount"][0], swap_received_currency)

    # Make swap row
    row = make_swap_tx_terra(txinfo, swap_sent_amount, swap_sent_currency, swap_received_amount, swap_received_currency)
    return [row]


def _handle_lp_stake(txinfo, from_contract):
    txid = txinfo.txid

    lp_currency = util_terra._lookup_lp_address(from_contract["lp_token"][0], txid)
    lp_amount = util_terra._float_amount(from_contract["share"][0], lp_currency)

    row = make_lp_stake_tx(txinfo, lp_amount, lp_currency)
    return [row]


def _handle_lp_unstake(txinfo, from_contract):
    txid = txinfo.txid

    # Determine lp currency
    index = from_contract["action"].index("burn")
    lp_currency_address = from_contract["contract_address"][index]
    lp_currency = util_terra._lookup_lp_address(lp_currency_address, txid)

    # Determine lp amount
    lp_amount = util_terra._float_amount(from_contract["withdraw_lp_amount"][0], lp_currency)

    row = make_lp_unstake_tx(txinfo, lp_amount, lp_currency)
    return [row]
