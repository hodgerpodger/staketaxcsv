
from staketaxcsv.common.ibc import constants as co
from staketaxcsv.common.ibc import make_tx, util_ibc
from staketaxcsv.common.ibc import denoms


def handle_simple(exporter, txinfo, msginfo):
    # row = make_tx.make_simple_tx(txinfo, msginfo)

    if txinfo.fee:
        row = make_tx.make_spend_tx_fee(txinfo, msginfo)
    else:
        row = make_tx.make_simple_tx(txinfo, msginfo)
    exporter.ingest_row(row)


def handle_unknown(exporter, txinfo, msginfo):
    row = make_tx.make_unknown_tx(txinfo, msginfo)
    exporter.ingest_row(row)


def handle_simple_outbound(exporter, txinfo, msginfo):
    """ Handles tx with 1 outbound transfer """
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 0 and len(transfers_out) == 1:
        amount, currency = transfers_out[0]
        row = make_tx.make_simple_tx_with_transfers(txinfo, msginfo, amount, currency, "", "")
        exporter.ingest_row(row)
        return

    handle_unknown(exporter, txinfo, msginfo)


def handle_staking(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    # Gather claim/rewards amount(s)
    totals = {}
    for amount, currency in transfers_in:
        if currency not in totals:
            totals[currency] = 0
        totals[currency] += amount

    delegate_comment = _comments_on_delegate(msginfo)

    if sum(totals.values()) > 0:
        i = 0
        for currency, total in totals.items():
            row = make_tx.make_reward_tx(txinfo, msginfo, total, currency)
            row.comment = f"claim reward in {msginfo.msg_type}{delegate_comment}"

            # Only first row should have fee (if exists)
            if i > 0:
                row.fee = ""
                row.fee_currency = ""
            i += 1

            exporter.ingest_row(row)
    else:
        # No reward: add non-income delegation transaction just so transaction doesn't appear "missing"
        row = make_tx.make_simple_tx(txinfo, msginfo)
        row.comment += delegate_comment
        exporter.ingest_row(row)


def _comments_on_delegate(msginfo):
    msg_type = msginfo.msg_type
    message = msginfo.message

    if msg_type == co.MSG_TYPE_DELEGATE:
        action = "delegated"
    elif msg_type == co.MSG_TYPE_REDELEGATE:
        action = "redelegated"
    elif msg_type == co.MSG_TYPE_UNDELEGATE:
        action = "undelegated"
    else:
        return ""

    if "amount" in message:
        amount_raw, currency_raw = message["amount"]["amount"], message["amount"]["denom"]
        amount, currency = denoms.amount_currency_from_raw(amount_raw, currency_raw, msginfo.lcd_node)
        return f" [{action} {amount} {currency}]"
    else:
        return f" [{action}]"


def handle_transfer_ibc(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_event
    _handle_transfer(exporter, txinfo, msginfo, transfers_in, transfers_out)


def handle_transfer(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_event
    _handle_transfer(exporter, txinfo, msginfo, transfers_in, transfers_out)


def _handle_transfer(exporter, txinfo, msginfo, transfers_in, transfers_out):
    if _is_self_transfer(msginfo):
        row = make_tx.make_self_transfer_tx(txinfo, msginfo)
        exporter.ingest_row(row)
        return
    elif len(transfers_in) == 1 and len(transfers_out) == 0:
        amount, currency, _, _ = transfers_in[0]
        row = make_tx.make_transfer_in_tx(txinfo, msginfo, amount, currency)
        exporter.ingest_row(row)
        return
    elif len(transfers_in) == 0 and len(transfers_out) == 1:
        amount, currency, source, dest = transfers_out[0]
        row = make_tx.make_transfer_out_tx(txinfo, msginfo, amount, currency, dest=dest)
        exporter.ingest_row(row)
        return
    elif len(transfers_in) == 0 and len(transfers_out) == 0:
        # ibc transfers can come in batches with unrelated transfers
        # omitting orw because too noisy to include non-related messages
        return
    elif len(transfers_in) > 0 or len(transfers_out) > 0:
        net_transfers_in, net_transfers_out = util_ibc.aggregate_transfers_net(transfers_in, transfers_out)

        for amount, currency in net_transfers_in:
            row = make_tx.make_transfer_in_tx(txinfo, msginfo, amount, currency)
            exporter.ingest_row(row)

        for amount, currency in net_transfers_out:
            row = make_tx.make_transfer_out_tx(txinfo, msginfo, amount, currency)
            exporter.ingest_row(row)
    else:
        handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def _is_self_transfer(msginfo):
    message = msginfo.message
    from_address = message.get("from_address")
    to_address = message.get("to_address")
    if from_address and (from_address == to_address):
        return True
    else:
        return False


def handle_multisend(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    i = 0
    for amount, currency in transfers_in:
        row = make_tx.make_transfer_in_tx(txinfo, msginfo, amount, currency)
        row.txid = row.txid + "-" + str(i)
        row.fee = "" if i > 0 else row.fee
        exporter.ingest_row(row)
        i += 1

    for amount, currency in transfers_out:
        row = make_tx.make_transfer_out_tx(txinfo, msginfo, amount, currency)
        row.txid = row.txid + "-" + str(i)
        row.fee = "" if i > 0 else row.fee
        exporter.ingest_row(row)
        i += 1


def unknown_txs_detect_transfers(txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    transfers_net_in, transfers_net_out = msginfo.transfers_net

    if len(transfers_in) == 0 and len(transfers_out) == 0:
        row = make_tx.make_unknown_tx(txinfo, msginfo)
        return [row]
    elif len(transfers_in) == 1 and len(transfers_out) == 1:
        # Present unknown transaction as one line (for this special case).
        sent_amount, sent_currency = transfers_out[0]
        received_amount, received_currency = transfers_in[0]

        row = make_tx.make_unknown_tx_with_transfer(
            txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        return [row]
    else:
        # Handle unknown transaction as separate transfers for each row.
        rows = []
        for sent_amount, sent_currency in transfers_net_out:
            rows.append(
                make_tx.make_unknown_tx_with_transfer(txinfo, msginfo, sent_amount, sent_currency, "", ""))
        for received_amount, received_currency in transfers_net_in:
            rows.append(
                make_tx.make_unknown_tx_with_transfer(txinfo, msginfo, "", "", received_amount, received_currency))
        return rows


def handle_unknown_detect_transfers(exporter, txinfo, msginfo):
    rows = unknown_txs_detect_transfers(txinfo, msginfo)
    util_ibc._ingest_rows(exporter, txinfo, msginfo, rows, "")


def handle_unknown_detect_transfers_tx(exporter, txinfo):
    for msginfo in txinfo.msgs:
        handle_unknown_detect_transfers(exporter, txinfo, msginfo)
