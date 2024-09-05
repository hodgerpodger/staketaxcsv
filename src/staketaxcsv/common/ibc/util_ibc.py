from collections import defaultdict
TINY_AMOUNT = 0.00000000001


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
        out.sort(key=lambda elem: elem["timestamp"], reverse=False)

    return out


def aggregate_transfers(transfers_list):
    sums_by_currency = defaultdict(float)

    for tup in transfers_list:
        amount, currency = tup[0], tup[1]
        sums_by_currency[currency] += amount

    out = []
    for currency, amount in sums_by_currency.items():
        out.append((amount, currency))
    return out


def aggregate_transfers_net(transfers_in, transfers_out, tiny_amount_filter=True):
    tiny_amount = TINY_AMOUNT if tiny_amount_filter else 0
    sums_by_currency = defaultdict(float)

    for tup in transfers_in:
        amount, currency = tup[0], tup[1]
        sums_by_currency[currency] += amount

    for tup in transfers_out:
        amount, currency = tup[0], tup[1]
        sums_by_currency[currency] -= amount

    net_transfers_in = []
    net_transfers_out = []

    for currency, amount in sums_by_currency.items():
        if amount > tiny_amount:
            net_transfers_in.append((amount, currency))
        elif amount < -tiny_amount:
            net_transfers_out.append((-amount, currency))

    return net_transfers_in, net_transfers_out
