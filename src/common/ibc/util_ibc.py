

def _msg_type(msginfo):
    # i.e. /osmosis.lockup.MsgBeginUnlocking -> _MsgBeginUnlocking
    last_field = msginfo.message["@type"].split(".")[-1]
    return last_field


def _ingest_rows(exporter, txinfo, msginfo, rows, comment):
    for i, row in enumerate(rows):
        row.comment = comment

        # Insert transaction fee for first csv row only
        if i == 0 and msginfo.msg_index == 0:
            row.fee = txinfo.fee
            row.fee_currency = txinfo.fee_currency
        else:
            row.fee = ""
            row.fee_currency = ""

        exporter.ingest_row(row)
