import logging


def _msg_type(msginfo):
    # i.e. /osmosis.lockup.MsgBeginUnlocking -> _MsgBeginUnlocking
    last_field = msginfo.message["@type"].split(".")[-1]
    return last_field


def _make_tx_type(msginfo):
    msg_type = _msg_type(msginfo)
    return "_" + msg_type


def _ingest_rows(exporter, rows, comment):
    for i, row in enumerate(rows):
        row.comment = comment
        if i > 0:
            row.fee, row.fee_currency = "", ""
        exporter.ingest_row(row)


def _period_lock_id(msginfo):
    msg_index = msginfo.msg_index
    log = msginfo.log

    # Extract period_lock_id value from events
    for event in log["events"]:
        event_type = event["type"]
        attributes = event["attributes"]

        if event_type in ["lock_tokens", "begin_unlock", "add_tokens_to_lock", "unlock"]:
            for kv in attributes:
                k, v = kv["key"], kv["value"]
                if k == "period_lock_id":
                    return v

    logging.error("Unable to find period_lock_id for msg_index=%s", msg_index)
