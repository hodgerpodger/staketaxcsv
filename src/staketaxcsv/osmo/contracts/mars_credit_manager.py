import logging

from staketaxcsv.osmo.make_tx import make_osmo_reward_tx
from staketaxcsv.common.make_tx import make_spend_fee_tx
from staketaxcsv.osmo.make_tx import (
    make_osmo_borrow_tx, make_osmo_repay_tx, make_osmo_swap_tx, make_mars_custom_tx,
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
        empty_fee = (action_index > 0) or (msginfo.msg_index > 0)

        if action_name == "borrow":
            _handle_borrow(exporter, txinfo, msginfo, empty_fee, action_index, account_id)
        elif action_name == "deposit":
            _handle_deposit(exporter, txinfo, msginfo, empty_fee, action_index, account_id)
        elif action_name == "lend":
            _handle_lend(exporter, txinfo, msginfo, empty_fee, action_index, account_id)
        elif action_name == "reclaim":
            _handle_reclaim(exporter, txinfo, msginfo, empty_fee, action_index, account_id)
        elif action_name == "repay":
            _handle_repay(exporter, txinfo, msginfo, empty_fee, action_index, account_id)
        elif action_name == "withdraw":
            _handle_withdraw(exporter, txinfo, msginfo, empty_fee, action_index, account_id)
        elif action_name == "swap_exact_in":
            _handle_swap_exact_in(exporter, txinfo, msginfo, empty_fee, action_index, account_id)
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


def _handle_deposit(exporter, txinfo, msginfo, empty_fee, action_index, account_id):
    deposit_amt, deposit_cur = _get_deposit_amount(msginfo)

    row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_MARS_DEPOSIT, empty_fee=empty_fee)
    row.comment += f"[mars_credit_manager deposit {deposit_amt} {deposit_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _get_deposit_amount(msginfo):
    events_as_dict = msginfo.events_as_dict

    for i, event in enumerate(events_as_dict):
        if event["event_type"] == "wasm" and event.get("action") == "rover/execute/update_credit_account":
            coin_deposited = event["coin_deposited"]
            deposit_amt, deposit_cur = msginfo.amount_currency(coin_deposited)[0]
            return deposit_amt, deposit_cur

    raise Exception("Unable to get deposit amount")


def _handle_borrow(exporter, txinfo, msginfo, empty_fee, action_index, account_id):
    borrow_amt, borrow_cur = _get_borrow_amount(msginfo)

    row = make_osmo_borrow_tx(txinfo, msginfo, borrow_amt, borrow_cur, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manager borrow {borrow_amt} {borrow_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _get_borrow_amount(msginfo):
    events_as_dict = msginfo.events_as_dict

    for i, event in enumerate(events_as_dict):
        if event["event_type"] == "wasm" and "coin_borrowed" in event:
            coin_borrowed = event["coin_borrowed"]
            borrow_amt, borrow_cur = msginfo.amount_currency(coin_borrowed)[0]
            return borrow_amt, borrow_cur

    raise Exception("Unable to get borrow amount")


def _handle_repay(exporter, txinfo, msginfo, empty_fee, action_index, account_id):
    repay_amt, repay_cur = _get_repay_amount(msginfo)

    row = make_osmo_repay_tx(txinfo, msginfo, repay_amt, repay_cur, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manager repay {repay_amt} {repay_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _get_repay_amount(msginfo):
    events_as_dict = msginfo.events_as_dict

    for i, event in enumerate(events_as_dict):
        if event["event_type"] == "wasm" and event.get("action", None) == "repay":
            coin_repaid = event["coin_repaid"]
            repay_amt, repay_cur = msginfo.amount_currency(coin_repaid)[0]
            return repay_amt, repay_cur

        if "coin_repaid" in event:
            coin_repaid = event["coin_repaid"]
            repay_amt, repay_cur = msginfo.amount_currency(coin_repaid)[0]
            return repay_amt, repay_cur

    raise Exception("Unable to get repay amount")


def _handle_withdraw(exporter, txinfo, msginfo, empty_fee, action_index, account_id):
    withdraw_amt, withdraw_cur = _get_withdraw_amount(msginfo)

    row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_MARS_WITHDRAW, empty_fee=empty_fee)
    row.comment += f"[mars_credit_manager withdraw {withdraw_amt} {withdraw_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _get_withdraw_amount(msginfo):
    events_as_dict = msginfo.events_as_dict

    for i, event in enumerate(events_as_dict):
        if event["event_type"] == "wasm" and event.get("action") == "withdraw":
            amount_raw = event["amount"]
            denom = event["denom"]
            withdraw_amt, withdraw_cur = msginfo.amount_currency(amount_raw + denom)[0]
            return withdraw_amt, withdraw_cur
        if event["event_type"] == "wasm" and event.get("action") == "callback/withdraw":
            coin_withdrawn = event["coin_withdrawn"]
            withdraw_amt, withdraw_cur = msginfo.amount_currency(coin_withdrawn)[0]
            return withdraw_amt, withdraw_cur

    raise Exception("Unable to get withdraw amount")


def _handle_lend(exporter, txinfo, msginfo, empty_fee, action_index, account_id):
    lend_amt, lend_cur = _get_lend_amount(msginfo)

    row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_MARS_LEND, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manager lend {lend_amt} {lend_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _get_lend_amount(msginfo):
    events_as_dict = msginfo.events_as_dict

    for i, event in enumerate(events_as_dict):
        if event["event_type"] == "wasm" and event.get("action", None) == "lend":

            event_after = events_as_dict[i + 1]
            if event_after["event_type"] == "coin_spent":
                lent_amount_raw = event_after["amount"]
                lend_amt, lend_cur = msginfo.amount_currency(lent_amount_raw)[0]
                return lend_amt, lend_cur
            elif event_after["event_type"] == "wasm" and event_after["action"] == "deposit":
                lent_amount_raw = event_after["amount"] + event_after["denom"]
                lend_amt, lend_cur = msginfo.amount_currency(lent_amount_raw)[0]
                return lend_amt, lend_cur

    raise Exception("Unable to get lend amount")


def _handle_reclaim(exporter, txinfo, msginfo, empty_fee, action_index, account_id):
    reclaim_amt, reclaim_cur = _get_reclaim_amount(msginfo)

    row = make_mars_custom_tx(txinfo, msginfo, tx_type=TX_TYPE_MARS_RECLAIM, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manager reclaim {reclaim_amt} {reclaim_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _get_reclaim_amount(msginfo):
    events_as_dict = msginfo.events_as_dict

    for i, event in enumerate(events_as_dict):
        if event["event_type"] == "wasm" and event.get("action", None) == "reclaim":
            coin_reclaimed = event["coin_reclaimed"]
            amt, cur = msginfo.amount_currency(coin_reclaimed)[0]
            return amt, cur

    raise Exception("Unable to get reclaim amount")


def _handle_swap_exact_in(exporter, txinfo, msginfo, empty_fee, action_index, account_id):
    sent_amt, sent_cur, rec_amt, rec_cur = _get_swap_amount(msginfo)

    row = make_osmo_swap_tx(txinfo, msginfo, sent_amt, sent_cur, rec_amt, rec_cur, empty_fee=empty_fee)
    row.comment += f" [mars_credit_manger swap {sent_amt} {sent_cur} for {rec_amt} {rec_cur}]"
    _export_action_row(exporter, row, action_index, account_id)


def _get_swap_amount(msginfo):
    events_as_dict = msginfo.events_as_dict
    sent_amt, sent_cur, rec_amt, rec_cur = None, None, None, None
    rec_denom = None

    # Get sent amt, cur
    for i, event in enumerate(events_as_dict):
        if event["event_type"] == "wasm" and event["action"] == "swapper":
            coin_in = event["coin_in"]
            denom_out = event["denom_out"]

            sent_amt, sent_cur = msginfo.amount_currency(coin_in)[0]
            rec_denom = denom_out
            break

    if not rec_denom:
        raise Exception("Unable to find rec_denom")

    # Get rec amt, cur
    for i, event in enumerate(events_as_dict):
        if event["event_type"] == "token_swapped":
            tokens_out = event["tokens_out"]
            if rec_denom in tokens_out:
                rec_amt, rec_cur = msginfo.amount_currency(tokens_out)[0]
                break

    logging.info("sent_amt:%s, sent_cur:%s, rec_amt:%s, rec_cur:%s", sent_amt, sent_cur, rec_amt, rec_cur)
    if sent_amt is not None and sent_cur is not None and rec_amt is not None and rec_cur is not None:
        return sent_amt, sent_cur, rec_amt, rec_cur

    raise Exception("Unable to get swap amount")
