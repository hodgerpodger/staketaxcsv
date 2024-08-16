from staketaxcsv.common.make_tx import make_borrow_tx, make_repay_tx
from staketaxcsv.osmo.make_tx import make_osmo_transfer_out_tx, make_osmo_transfer_in_tx


def handle_red_bank(exporter, txinfo, msginfo):
    msg = msginfo.execute_contract_message

    if "deposit" in msg:
        return _handle_deposit(exporter, txinfo, msginfo)
    if "withdraw" in msg:
        return _handle_withdraw(exporter, txinfo, msginfo)
    if "borrow" in msg:
        return _handle_borrow(exporter, txinfo, msginfo)
    if "repay" in msg:
        return _handle_repay(exporter, txinfo, msginfo)

    raise Exception("Unable to handle tx in mars_red_bank.handle_red_bank()")


def _handle_deposit(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_out) == 1 and len(transfers_in) == 0:
        sent_amt, sent_cur = transfers_out[0]

        row = make_osmo_transfer_out_tx(txinfo, msginfo, sent_amt, sent_cur)
        row.comment += f"[mars_red_bank deposit {sent_amt} {sent_cur}]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in mars_red_bank._handle_deposit()")


def _handle_withdraw(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        rec_amt, rec_cur = transfers_in[0]

        row = make_osmo_transfer_in_tx(txinfo, msginfo, rec_amt, rec_cur)
        row.comment += f"[mars_red_bank withdraw {rec_amt} {rec_cur}]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in mars_red_bank._handle_deposit()")


def _handle_repay(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net

    if len(transfers_out) == 1 and len(transfers_in) == 0:
        sent_amt, sent_cur = transfers_out[0]

        row = make_repay_tx(txinfo, sent_amt, sent_cur)
        row.comment += f" [mars_red_bank repay {sent_amt} {sent_cur}]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in mars_red_bank._handle_repay()")


def _handle_borrow(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        rec_amt, rec_cur = transfers_in[0]

        row = make_borrow_tx(txinfo, rec_amt, rec_cur)
        row.comment += f" [mars_red_bank borrow {rec_amt} {rec_cur}]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in mars_red_bank._handle_borrow()")
