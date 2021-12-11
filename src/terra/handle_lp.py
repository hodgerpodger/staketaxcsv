
from terra import util_terra
from terra.make_tx import (
    make_lp_deposit_tx, make_lp_withdraw_tx, make_lp_stake_tx, make_lp_unstake_tx,
    make_withdraw_collateral_tx, make_deposit_collateral_tx)
from terra.constants import CUR_UST


def handle_lp_deposit(exporter, elem, txinfo):
    txid = txinfo.txid
    from_contract = util_terra._event_with_action(elem, "from_contract", "provide_liquidity")

    # Determine LP currency
    lp_currency_address = _extract_contract_address(txid, from_contract, "mint")
    lp_currency, _ = util_terra._lookup_lp_address(lp_currency_address, txid)

    # Determine received LP amount
    lp_amount_string = from_contract["share"][0]
    lp_amount = util_terra._float_amount(lp_amount_string, lp_currency)

    # Determine sent collateral
    deposits = _extract_collateral_amounts(txid, from_contract, "assets")

    # Create two LP_DEPOSIT rows
    i = 0
    for currency, amount in deposits:
        row = make_lp_deposit_tx(
            txinfo, amount, currency, lp_amount / len(deposits), lp_currency, txid, empty_fee=(i > 0))
        exporter.ingest_row(row)
        i += 1


def handle_lp_withdraw(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    from_contract = util_terra._event_with_action(elem, "from_contract", "withdraw_liquidity")

    # Determine LP currenecy
    lp_currency_address = _extract_contract_address(txid, from_contract, "send")
    lp_currency, _ = util_terra._lookup_lp_address(lp_currency_address, txid)

    # Determine sent LP amount
    lp_amount_string = from_contract["withdrawn_share"][0]
    lp_amount = util_terra._float_amount(lp_amount_string, lp_currency)

    # Create _LP_WITHDRAW rows
    _handle_withdraw_collaterals(exporter, txinfo, lp_amount, lp_currency, elem, from_contract, wallet_address)


def handle_lp_withdraw_idx(exporter, elem, txinfo):
    txid = txinfo.txid
    from_contract = util_terra._event_with_action(elem, "from_contract", "withdraw")

    withdraw_amount = from_contract["withdraw_amount"][0]
    amount, currency = util_terra._amount(withdraw_amount)

    row = make_withdraw_collateral_tx(txinfo, amount, currency)
    exporter.ingest_row(row)


def handle_lp_deposit_idx(exporter, elem, txinfo):
    txid = txinfo.txid
    from_contract = util_terra._event_with_action(elem, "from_contract", "deposit")

    deposit_amount = from_contract["deposit_amount"][0]
    amount, currency = util_terra._amount(deposit_amount)

    row = make_deposit_collateral_tx(txinfo, amount, currency)
    exporter.ingest_row(row)


def _handle_withdraw_collaterals(exporter, txinfo, lp_amount, lp_currency, data, from_contract, wallet_address):
    txid = txinfo.txid

    # Determine received collateral
    withdraws = _extract_collateral_amounts(txid, from_contract, "refund_assets")

    # Create two LP_WITHDRAW rows
    i = 0
    for currency, amount in withdraws:
        # Adjust UST withdrawal amount to account for small fee
        if currency == CUR_UST:
            result = _check_ust_adjustment(data, wallet_address, txid)
            if result:
                amount = result

        row = make_lp_withdraw_tx(
            txinfo, lp_amount / len(withdraws), lp_currency, amount, currency, txid, empty_fee=(i > 0))
        exporter.ingest_row(row)
        i += 1


def _check_ust_adjustment(data, wallet_address, txid):
    transfers_in, transfers_out = util_terra._transfers(data, wallet_address, txid)

    if transfers_in:
        for amount, currency in transfers_in:
            if currency == CUR_UST:
                return amount
    return None


def _extract_contract_address(txid, from_contract, action):
    actions = from_contract["action"]
    contract_addresses = from_contract["contract_address"]

    for i in range(len(actions)):
        if actions[i] == action:
            return contract_addresses[i]

    raise Exception("Bad condition _extract_address_for_action() action={} txid={}".format(action, txid))


def _extract_collateral_amounts(txid, from_contract, asset_field):
    assets = from_contract[asset_field]

    result = {}
    for amounts_string in assets:
        result.update(util_terra._extract_amounts(amounts_string))

    if len(result) == 0:
        raise Exception("Unable to extract amounts/currencies in lp transaction for txid=%s", txid)

    out = []
    for currency, amount in result.items():
        out.append([currency, amount])

    return out


def handle_lp_stake(exporter, elem, txinfo):
    txid = txinfo.txid

    # Determine LP currency
    lp_currency_address = util_terra._contract(elem)
    lp_currency, _ = util_terra._lookup_lp_address(lp_currency_address, txid)
    if not lp_currency:
        raise Exception("Bad condition handle_lp_stake() txid=%s", txid)

    # Determine LP amount
    execute_msg = util_terra._execute_msg(elem)
    lp_amount = util_terra._float_amount(execute_msg["send"]["amount"], lp_currency)

    row = make_lp_stake_tx(txinfo, lp_amount, lp_currency)
    exporter.ingest_row(row)


def handle_lp_stake_deposit_strategy(exporter, elem, txinfo):
    txid = txinfo.txid
    from_contract = util_terra._event_with_action(elem, "from_contract", "deposit_to_strategy")
    execute_msg = util_terra._execute_msg(elem)

    # Determine LP currency
    lp_currency_address = from_contract["lp_token"][0]
    lp_currency, _ = util_terra._lookup_lp_address(lp_currency_address, txid)

    # Determine LP amount
    lp_amount = util_terra._float_amount(execute_msg["send"]["amount"], lp_currency)

    row = make_lp_stake_tx(txinfo, lp_amount, lp_currency)
    exporter.ingest_row(row)


def handle_lp_unstake(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Determine LP currency
    lp_currency_address = elem["logs"][0]["events_by_type"]["execute_contract"]["contract_address"][0]
    lp_currency, _ = util_terra._lookup_lp_address(lp_currency_address, txid)
    if not lp_currency:
        raise Exception("Bad condition handle_lp_stake() txid=%s", txid)

    # Determine LP amount
    execute_msg = util_terra._execute_msg(elem)
    lp_amount = util_terra._float_amount(execute_msg["unbond"]["amount"], lp_currency)

    # Create _LP_UNSTAKE row
    row = make_lp_unstake_tx(txinfo, lp_amount, lp_currency)
    exporter.ingest_row(row)

    # Create _LP_WITHDRAW rows (if withdraw exists)
    from_contract = util_terra._event_with_action(elem, "from_contract", "withdraw_liquidity")
    if from_contract:
        _handle_withdraw_collaterals(exporter, txinfo, lp_amount, lp_currency, elem, from_contract, wallet_address)


def handle_lp_unstake_withdraw_from_strategy(exporter, elem, txinfo):
    txid = txinfo.txid
    from_contract = elem["logs"][0]["events_by_type"]["from_contract"]

    # Determine LP currency
    lp_currency_address = from_contract["lp_token"][0]
    lp_currency, _ = util_terra._lookup_lp_address(lp_currency_address, txid)
    if not lp_currency:
        raise Exception("Bad condition handle_lp_unstake_withdraw() txid=%s", txid)

    # Determine LP amount
    lp_amount = util_terra._float_amount(from_contract["withdraw_lp_amount"][0], lp_currency)

    # Create _LP_UNSTAKE row
    row = make_lp_unstake_tx(txinfo, lp_amount, lp_currency)
    exporter.ingest_row(row)


def handle_lp_long_farm(exporter, elem, txinfo):
    txid = txinfo.txid
    from_contract = util_terra._event_with_action(elem, "from_contract", "provide_liquidity")

    # Determine sent collateral
    deposits = _extract_collateral_amounts(txid, from_contract, "assets")

    # Determine LP currency
    lp_currency_address = _extract_contract_address(txid, from_contract, "mint")
    lp_currency, _ = util_terra._lookup_lp_address(lp_currency_address, txid)

    # Determine received LP amount
    lp_amount = util_terra._float_amount(from_contract["share"][0], lp_currency)

    # Create two LP_DEPOSIT rows
    i = 0
    for currency, amount in deposits:
        row = make_lp_deposit_tx(txinfo, amount, currency, lp_amount / len(deposits), lp_currency, txid,
                                 empty_fee=(i > 0), z_index=i)
        exporter.ingest_row(row)
        i += 1

    # Create one LP_STAKE row
    row = make_lp_stake_tx(txinfo, lp_amount, lp_currency, empty_fee=True, z_index=i)
    exporter.ingest_row(row)
