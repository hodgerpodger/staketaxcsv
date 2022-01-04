
from terra import util_terra
from terra.make_tx import (
    make_lp_deposit_tx, make_lp_withdraw_tx, make_lp_stake_tx, make_lp_unstake_tx,
    make_withdraw_collateral_tx, make_deposit_collateral_tx)
from common.make_tx import make_transfer_out_tx, make_transfer_in_tx
from terra.constants import CUR_UST
from terra.config_terra import localconfig


def handle_lp_deposit(exporter, elem, txinfo):
    comment = "liquidity pool deposit"
    from_contract = util_terra._event_with_action(elem, "from_contract", "provide_liquidity")

    rows = _handle_lp_deposit(txinfo, from_contract)
    util_terra._ingest_rows(exporter, rows, comment)


def _handle_lp_deposit(txinfo, from_contract):
    txid = txinfo.txid
    rows = []

    # Determine LP currency
    lp_currency_address = _extract_contract_address(txid, from_contract, "mint")
    lp_currency, _ = util_terra._lookup_lp_address(lp_currency_address, txid)

    # Determine received LP amount
    lp_amount_string = from_contract["share"][0]
    lp_amount = util_terra._float_amount(lp_amount_string, lp_currency)

    # Determine sent collateral
    deposits = _extract_collateral_amounts(txid, from_contract, "assets")

    if localconfig.lp:
        # Optional setting: treat LP deposit as 2 outbound transfers and 1 lp token receive
        currency1, amount1 = deposits[0]
        currency2, amount2 = deposits[1]

        row = make_transfer_out_tx(txinfo, amount1, currency1)
        rows.append(row)
        row = make_transfer_out_tx(txinfo, amount2, currency2)
        rows.append(row)

        row = make_lp_deposit_tx(txinfo, "", "", lp_amount, lp_currency, txid)
        rows.append(row)

        return rows
    else:
        # Default: create two LP_DEPOSIT rows
        i = 0
        for currency, amount in deposits:
            row = make_lp_deposit_tx(
                txinfo, amount, currency, lp_amount / len(deposits), lp_currency, txid, empty_fee=(i > 0))
            rows.append(row)
            i += 1
        return rows


def handle_lp_withdraw(exporter, elem, txinfo):
    comment = "liquidity pool withdraw"
    from_contract = util_terra._event_with_action(elem, "from_contract", "withdraw_liquidity")

    rows = _handle_lp_withdraw(elem, txinfo, from_contract)

    for i, row in enumerate(rows):
        row.comment = comment
        if i > 0:
            row.fee, row.fee_currency = "", ""
        exporter.ingest_row(row)


def _handle_lp_withdraw(elem, txinfo, from_contract):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Determine LP currenecy
    lp_currency_address = _extract_contract_address(txid, from_contract, "send")
    lp_currency, _ = util_terra._lookup_lp_address(lp_currency_address, txid)

    # Determine sent LP amount
    lp_amount_string = from_contract["withdrawn_share"][0]
    lp_amount = util_terra._float_amount(lp_amount_string, lp_currency)

    # Create _LP_WITHDRAW rows
    rows = _handle_withdraw_collaterals(txinfo, lp_amount, lp_currency, elem, from_contract)
    return rows


def handle_lp_withdraw_idx(exporter, elem, txinfo):
    from_contract = util_terra._event_with_action(elem, "from_contract", "withdraw")

    withdraw_amount = from_contract["withdraw_amount"][0]
    amount, currency = util_terra._amount(withdraw_amount)

    row = make_withdraw_collateral_tx(txinfo, amount, currency)
    exporter.ingest_row(row)


def handle_lp_deposit_idx(exporter, elem, txinfo):
    from_contract = util_terra._event_with_action(elem, "from_contract", "deposit")

    deposit_amount = from_contract["deposit_amount"][0]
    amount, currency = util_terra._amount(deposit_amount)

    row = make_deposit_collateral_tx(txinfo, amount, currency)
    exporter.ingest_row(row)


def _handle_withdraw_collaterals(txinfo, lp_amount, lp_currency, data, from_contract):
    rows = []
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Determine received collateral
    withdraws = _extract_collateral_amounts(txid, from_contract, "refund_assets")

    if localconfig.lp:
        # Optional setting: treat lp withdraw as 2 inbound transfers and 1 lp token send

        # 2 inbound transfers
        i = 0
        for currency, amount in withdraws:
            amount, currency = _check_ust_adjustment(amount, currency, data, wallet_address, txid)
            row = make_transfer_in_tx(txinfo, amount, currency)
            rows.append(row)
            i += 1

        # 1 lp token send
        row = make_lp_withdraw_tx(txinfo, lp_amount, lp_currency, "", "", txid)
        rows.append(row)
        return rows
    else:
        # Default: create two LP_WITHDRAW rows

        i = 0
        for currency, amount in withdraws:
            # Adjust UST withdrawal amount to account for small fee
            amount, currency = _check_ust_adjustment(amount, currency, data, wallet_address, txid)

            row = make_lp_withdraw_tx(
                txinfo, lp_amount / len(withdraws), lp_currency, amount, currency, txid, empty_fee=(i > 0))
            rows.append(row)
            i += 1
        return rows


def _check_ust_adjustment(amount, currency, data, wallet_address, txid):
    """ Adjusts UST inbound transfer amount if UST fee """
    if currency != CUR_UST:
        return amount, currency

    transfers_in, transfers_out = util_terra._transfers(data, wallet_address, txid)
    if transfers_in:
        for amt, cur in transfers_in:
            if cur == CUR_UST:
                return amt, cur

    return amount, currency


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
        rows = _handle_withdraw_collaterals(txinfo, lp_amount, lp_currency, elem, from_contract)
        util_terra._ingest_rows(exporter, rows, "")


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
