

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


def remove_duplicates(elems, tx_hash_key="txhash", timestamp_sort=True):
    out = []
    txids = set()

    for elem in elems:
        if elem[tx_hash_key] in txids:
            continue

        out.append(elem)
        txids.add(elem[tx_hash_key])

    if timestamp_sort:
        out.sort(key=lambda elem: elem["timestamp"], reverse=True)

    return out
