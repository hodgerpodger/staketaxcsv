import logging

from staketaxcsv.osmo.make_tx import make_osmo_reward_tx
from staketaxcsv.common.make_tx import make_spend_fee_tx, make_unknown_tx
from staketaxcsv.settings_csv import OSMO_NODE
from staketaxcsv.osmo import denoms
from staketaxcsv.osmo.make_tx import (
    make_osmo_transfer_out_tx, make_osmo_transfer_in_tx, make_osmo_borrow_tx,
    make_osmo_repay_tx, make_osmo_tx,
    make_osmo_swap_tx, make_mars_custom_tx,
)
from staketaxcsv.common.ExporterTypes import (
    TX_TYPE_MARS_CREATE_CREDIT_ACCOUNT, TX_TYPE_MARS_RECLAIM, TX_TYPE_MARS_LEND, TX_TYPE_UNKNOWN,
    TX_TYPE_MARS_DEPOSIT, TX_TYPE_MARS_WITHDRAW,
)


def handle_claim_rewards(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        received_amount, received_currency = transfers_in[0]

        row = make_osmo_reward_tx(txinfo, msginfo, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in handle_mars.handle_claim_rewards()")


def handle_credit_manager(exporter, txinfo, msginfo):
    msg = msginfo.execute_contract_message

    if "create_credit_account" in msg:
        return _handle_create_credit_account(exporter, txinfo, msginfo)
    elif "update_credit_account" in msg:
        return _handle_update_credit_account(exporter, txinfo, msginfo)
    elif "repay_from_wallet" in msg:
        return _handle_repay_from_wallet(exporter, txinfo, msginfo)

    raise Exception("Unable to handle tx in mars_credit_manager.handle_credit_manager()")


def _handle_create_credit_account(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 0 and len(transfers_out) == 0:
        if msginfo.msg_index == 0:
            row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)
        else:
            row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_MARS_CREATE_CREDIT_ACCOUNT, empty_fee=True)
        row.comment = "[mars create credit account]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in mars_credit_manager._handle_create_credit_account()")


def _handle_repay_from_wallet(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    account_id = msginfo.execute_contract_message["repay_from_wallet"]["account_id"]

    if len(transfers_out) == 1 and len(transfers_in) == 0:
        sent_amt, sent_cur = transfers_out[0]
        row = make_osmo_repay_tx(txinfo, msginfo, sent_amt, sent_cur)
        row.comment += f" [mars_credit_manager repay_from_wallet {sent_amt} {sent_cur}][account_id={account_id}]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in mars_credit_manager._handle_repay_from_wallet()")


def _handle_update_credit_account(exporter, txinfo, msginfo):
    account_id = msginfo.execute_contract_message["update_credit_account"].get("account_id", "")
    actions = msginfo.execute_contract_message["update_credit_account"]["actions"]
    logging.info("actions:")
    logging.info(actions)

    has_error = False
    for action_index, action in enumerate(actions):
        if len(action) > 1:
            raise Exception("Unexpected format for action: %s", action)

        action_name = list(action.keys())[0]
        action_info = action[action_name]
        empty_fee = (action_index > 0) or (msginfo.msg_index > 0)

        if action_name == "borrow":
            _handle_borrow(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id)
        elif action_name == "deposit":
            _handle_deposit(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id)
        elif action_name == "lend":
            _handle_lend(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id)
        elif action_name == "reclaim":
            _handle_reclaim(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id)
        elif action_name == "repay":
            _handle_repay(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id)
        elif action_name == "withdraw":
            _handle_withdraw(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id)
        elif action_name == "swap_exact_in":
            _handle_swap_exact_in(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id)
        else:
            row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_UNKNOWN, empty_fee=empty_fee)
            row.comment += f"[mars_credit_manager unknown action {action_name}][account_id={account_id}]"
            _export_action_row(exporter, row, action_index, account_id)

            has_error = True

    if has_error:
        raise Exception("Unable to fully handle transactions in mars_credit_manager._handle_update_credit_account")


def _export_action_row(exporter, row, action_index, account_id):
    row.z_index = action_index
    row.txid += f"-{action_index}"
    row.comment += f"[account_id={account_id}]"
    exporter.ingest_row(row)


def _handle_deposit(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id):
    deposit_amt, deposit_cur = _get_amount_for_action("deposit", action_info, msginfo)

    row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_MARS_DEPOSIT, empty_fee=empty_fee)
    row.comment += f"[mars_credit_manager deposit {deposit_amt} {deposit_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _handle_borrow(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id):
    borrow_amt, borrow_cur = _get_amount_for_action("borrow", action_info, msginfo)

    row = make_osmo_borrow_tx(txinfo, msginfo, borrow_amt, borrow_cur, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manager borrow {borrow_amt} {borrow_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _handle_repay(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id):
    repay_amt, repay_cur = _get_amount_for_action("repay", action_info, msginfo)

    row = make_osmo_repay_tx(txinfo, msginfo, repay_amt, repay_cur, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manager repay {repay_amt} {repay_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _handle_withdraw(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id):
    withdraw_amt, withdraw_cur = _get_amount_for_action("withdraw", action_info, msginfo)

    row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_MARS_WITHDRAW, empty_fee=empty_fee)
    row.comment += f"[mars_credit_manager withdraw {withdraw_amt} {withdraw_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _handle_lend(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id):
    _, lend_cur = _get_amount_for_action("lend", action_info, msginfo)

    row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_MARS_LEND, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manager lend {lend_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _handle_reclaim(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id):
    reclaim_amt, reclaim_cur = _get_amount_for_action("reclaim", action_info, msginfo)

    row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_MARS_RECLAIM, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manager reclaim {reclaim_amt} {reclaim_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _handle_swap_exact_in(exporter, txinfo, msginfo, action_info, empty_fee, action_index, account_id):
    sent_amt, sent_cur = _get_amount_for_action("swap_exact_in", action_info["coin_in"], msginfo)
    rec_amt_raw = _get_amount_raw_from_wasm("swap_exact_in", msginfo)
    rec_denom = action_info["denom_out"]
    rec_amt, rec_cur = denoms.amount_currency_from_raw(rec_amt_raw, rec_denom, OSMO_NODE)

    row = make_osmo_swap_tx(txinfo, msginfo, sent_amt, sent_cur, rec_amt, rec_cur, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manger swap {sent_amt} {sent_cur} for {rec_amt} {rec_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _get_amount_for_action(action_name, action_info, msginfo):
    """
    Retrieves the amount and currency for a given action (borrow, deposit, etc.)
    from either the action_info or the wasm event data.
    """
    if "coin" in action_info:
        action_info = action_info["coin"]

    # Find denom
    denom = action_info["denom"]

    # Find amount
    if action_info["amount"] == "account_balance":
        # special cases
        if action_name == "withdraw":
            # i.e. 383886ibc/D79E7D83AB399BFFF93433E54FAA480C191248FC556924A2A8351AE2638B3877
            coin_withdrawn = msginfo.events_by_type["wasm"]["coin_withdrawn"]
            withdraw_amt, withdraw_cur = msginfo.amount_currency(coin_withdrawn)[0]
            return withdraw_amt, withdraw_cur

        if action_name == "repay":
            coin_repaid = msginfo.events_by_type["wasm"]["coin_repaid"]
            repay_amt, repay_cur = msginfo.amount_currency(coin_repaid)[0]
            return repay_amt, repay_cur

        amount_raw = _get_amount_raw_from_wasm(action_name, msginfo)
    else:
        if isinstance(action_info["amount"], dict) and "exact" in action_info["amount"]:
            amount_raw = action_info["amount"]["exact"]
        else:
            amount_raw = action_info["amount"]

    # Convert the raw amount and denom to the formatted amount and currency
    amount, currency = denoms.amount_currency_from_raw(amount_raw, denom, OSMO_NODE)

    return amount, currency


def _get_amount_raw_from_wasm(target_action_name, msginfo):
    events_by_type = msginfo.events_by_type
    actions = msginfo.execute_contract_message["update_credit_account"]["actions"]

    # comma-delimited element
    amounts = events_by_type["wasm"]["amount"].split(",")

    # choose amount from list based on where action_name exists in actions element
    cur_index = 0
    for action in actions:
        action_name = list(action.keys())[0]
        action_info = action[action_name]

        if action_name == target_action_name:
            return amounts[cur_index]

        if "amount" in action_info or "amount" in action_info.get("coin_in", {}):
            cur_index += 1

    raise Exception("Bad condition: unable to retrieve index in _get_amount_from_wasm()")
