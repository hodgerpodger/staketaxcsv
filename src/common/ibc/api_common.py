TXS_LIMIT_PER_QUERY = 50
EVENTS_TYPE_SENDER = "sender"
EVENTS_TYPE_RECIPIENT = "recipient"
EVENTS_TYPE_SIGNER = "signer"
EVENTS_TYPE_LIST_DEFAULT = [
    EVENTS_TYPE_SENDER,
    EVENTS_TYPE_RECIPIENT,
]


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
