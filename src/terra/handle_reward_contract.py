from common.ErrorCounter import ErrorCounter
from common.make_tx import make_airdrop_tx, make_reward_tx, make_unknown_tx
from terra import util_terra
from terra.config_terra import localconfig
from terra.constants import CUR_ANC, CUR_MINE, CUR_MIR
from terra.handle_reward import REWARD_CURRENCIES

CONTRACTS_AIRDROP = {
    "terra1kalp2knjm4cs3f59ukr4hdhuuncp648eqrgshw": CUR_MIR,
    "terra146ahqn6d3qgdvmj8cj96hh03dzmeedhsf0kxqm": CUR_ANC,
    "terra1ud39n6c42hmtp2z0qmy8svsk7z3zmdkxzfwcf2": CUR_MINE
}


def handle_airdrop(exporter, elem, txinfo):
    msgs = elem["tx"]["value"]["msg"]
    for index, msg in enumerate(msgs):
        msg_type = msg["type"]

        if msg_type == "wasm/MsgExecuteContract":
            _handle_airdrop(exporter, elem, txinfo, index)
        elif msg_type == "distribution/MsgWithdrawDelegationReward":
            _handle_withdraw_rewards(exporter, elem, txinfo, index)


def _handle_withdraw_rewards(exporter, elem, txinfo, index):
    txid = txinfo.txid

    withdraw_rewards = elem["logs"][index]["events_by_type"]["withdraw_rewards"]
    amount_string = withdraw_rewards["amount"][0]

    for amount, currency in util_terra._amounts(amount_string):
        # Skip minor currencies if option set
        if not localconfig.minor_rewards and currency not in REWARD_CURRENCIES:
            continue

        row_txid = "{}-{}".format(txid, index) if index else txid
        row = make_reward_tx(txinfo, amount, currency, txid=row_txid, empty_fee=(index > 0))
        exporter.ingest_row(row)


def _handle_airdrop(exporter, elem, txinfo, index):
    txid = txinfo.txid

    # Get currency
    contract = util_terra._contract(elem, index)
    if contract in CONTRACTS_AIRDROP:
        # Hardcoded to save a lookup
        currency = CONTRACTS_AIRDROP[contract]
    else:
        currency = _lookup_airdrop_currency(txid, elem, index)
        if not currency:
            ErrorCounter.increment("handle_airdrop_error_unknown", txid)
            row = make_unknown_tx(txinfo)
            exporter.ingest_row(row)
            return

    # Get amount
    amount = _extract_amount(elem, index, currency)

    # Detect outgoing transfers as fees for reporting
    _detect_contract_fee(txinfo, elem)

    row_txid = "{}-{}".format(txid, index) if index else txid
    row = make_airdrop_tx(txinfo, amount, currency, row_txid, empty_fee=index > 0)
    exporter.ingest_row(row)


def _detect_contract_fee(txinfo, elem):
    # Detect outgoing transfer event in airdrop contract and add as fee for reporting.
    _, transfers_out = util_terra._transfers(elem, txinfo.wallet_address, txinfo.txid)

    if len(transfers_out) == 1:
        amount, currency = transfers_out[0]
        if currency == txinfo.fee_currency and amount < 5:
            txinfo.fee += amount


def _extract_amount(elem, index, currency):
    # Get amount
    try:
        execute_msg = util_terra._execute_msg(elem, index)
        amount = util_terra._float_amount(execute_msg["claim"]["amount"], currency)
        return amount
    except Exception:
        pass

    try:
        from_contract = util_terra._event_with_action(elem, "from_contract", "claim")
        amounts = from_contract["amount"]
        actions = from_contract["action"]
        for i in range(len(amounts)):
            action = actions[i]
            amount = amounts[i]

            if action == "claim":
                return util_terra._float_amount(amount, currency)
    except Exception:
        pass

    raise Exception("Unable to extract amount")


def _lookup_airdrop_currency(txid, data, index):
    from_contract = data["logs"][index]["events_by_type"]["from_contract"]

    for i in range(len(from_contract['action'])):
        action = from_contract['action'][i]
        contract_address = from_contract['contract_address'][i]

        if action == "transfer":
            currency, _ = util_terra._lookup_address(contract_address, txid)
            return currency
    return None


def handle_reward_contract(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address

    # Check transfer event for reward
    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid)
    if transfers_in:
        amount, currency = transfers_in[0]
        row = make_reward_tx(txinfo, amount, currency)
        exporter.ingest_row(row)
        return

    logs = elem["logs"]
    for i, log in enumerate(logs):
        from_contract = log["events_by_type"]["from_contract"]
        if i == 0:
            txid_row = txid
        else:
            txid_row = "{}-{}".format(txid, i)

        # Try "claim_amount" field
        try:
            currency = _get_currency(from_contract, txid)
            amount = util_terra._float_amount(from_contract["claim_amount"][0], currency)
            row = make_reward_tx(txinfo, amount, currency, txid=txid_row, empty_fee=i > 0)
            exporter.ingest_row(row)
            continue
        except Exception:
            pass

        # Try "amount" field
        try:
            currency = _get_currency(from_contract, txid)
            amount = util_terra._float_amount(from_contract["amount"][0], currency)
            if amount <= 0:
                continue

            row = make_reward_tx(txinfo, amount, currency, txid=txid_row)
            exporter.ingest_row(row)
            continue
        except Exception:
            pass

        ErrorCounter.increment("handle_claim_rewards_unknown", txid=txid_row)
        row = make_unknown_tx(txinfo)
        exporter.ingest_row(row)


def _get_currency(from_contract, txid):
    for i in range(len(from_contract["action"])):
        action = from_contract["action"][i]
        contract_address = from_contract["contract_address"][i]

        if action == "transfer":
            currency, _ = util_terra._lookup_address(contract_address, txid)
            return currency

    raise Exception("_get_currency(): unable to determine currency txid={}".format(txid))
