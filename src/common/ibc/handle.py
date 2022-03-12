
from common.ibc import make_tx
from common.ibc import util_ibc


def handle_simple(exporter, txinfo, msginfo):
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

    total = 0
    for amount, currency in transfers_in:
        total += amount

    if total > 0:
        row = make_tx.make_reward_tx(txinfo, msginfo, total, currency)
        row.comment = "claim reward in {}".format(msginfo.msg_type)
        exporter.ingest_row(row)
    else:
        # No reward: add non-income delegation transaction just so transaction doesn't appear "missing"
        row = make_tx.make_simple_tx(txinfo, msginfo)
        exporter.ingest_row(row)


def handle_transfer_ibc(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_event
    _handle_transfer(exporter, txinfo, msginfo, transfers_in, transfers_out)


def handle_transfer(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_event
    _handle_transfer(exporter, txinfo, msginfo, transfers_in, transfers_out)


def _handle_transfer(exporter, txinfo, msginfo, transfers_in, transfers_out):
    if len(transfers_in) == 1 and len(transfers_out) == 0:
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
    else:
        handle_unknown_detect_transfers(exporter, txinfo, msginfo)


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


def handle_unknown_detect_transfers(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 0 and len(transfers_out) == 0:
        handle_unknown(exporter, txinfo, msginfo)
        return
    elif len(transfers_in) == 1 and len(transfers_out) == 1:
        # Present unknown transaction as one line (for this special case).
        sent_amount, sent_currency = transfers_out[0]
        received_amount, received_currency = transfers_in[0]

        row = make_tx.make_unknown_tx_with_transfer(
            txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    else:
        # Handle unknown transaction as separate transfers for each row.
        rows = []
        for sent_amount, sent_currency in transfers_out:
            rows.append(
                make_tx.make_unknown_tx_with_transfer(txinfo, msginfo, sent_amount, sent_currency, "", ""))
        for received_amount, received_currency in transfers_in:
            rows.append(
                make_tx.make_unknown_tx_with_transfer(txinfo, msginfo, "", "", received_amount, received_currency))
        util_ibc._ingest_rows(exporter, txinfo, msginfo, rows, "")
