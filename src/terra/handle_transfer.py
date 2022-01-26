from common.ErrorCounter import ErrorCounter
from common.make_tx import make_transfer_in_tx, make_transfer_out_tx
from terra import util_terra
from terra.handle_simple import handle_unknown, handle_unknown_detect_transfers


def handle_transfer(exporter, elem, txinfo):
    wallet_address = txinfo.wallet_address

    msgs = elem["tx"]["value"]["msg"]
    for msg in msgs:
        if msg["type"] != "bank/MsgSend":
            continue

        from_address = msg["value"]["from_address"]
        to_address = msg["value"]["to_address"]

        for amount in msg["value"]["amount"]:
            denom = amount["denom"]
            amount_string = amount["amount"]

            currency = util_terra._denom_to_currency(denom)
            amount = util_terra._float_amount(amount_string, None)

            if wallet_address == from_address:
                row = make_transfer_out_tx(txinfo, amount, currency, to_address)
                exporter.ingest_row(row)
            elif wallet_address == to_address:
                row = make_transfer_in_tx(txinfo, amount, currency)
                exporter.ingest_row(row)
            else:
                continue


def handle_transfer_contract(exporter, elem, txinfo):
    txid = txinfo.txid
    wallet_address = txinfo.wallet_address
    execute_msg = util_terra._execute_msg(elem)

    recipient = execute_msg["transfer"].get("recipient", None)
    if recipient:
        # Extract amount
        amount = util_terra._float_amount(execute_msg["transfer"]["amount"], None)

        # Extract currency
        msg_value = elem["tx"]["value"]["msg"][0]["value"]
        contract = msg_value.get("contract")
        sender = msg_value.get("sender")
        currency, _ = util_terra._lookup_address(contract, txid)

        if sender == wallet_address:
            row = make_transfer_out_tx(txinfo, amount, currency, recipient)
            exporter.ingest_row(row)
        elif recipient == wallet_address:
            row = make_transfer_in_tx(txinfo, amount, currency)
            exporter.ingest_row(row)
    else:
        handle_unknown(exporter, txinfo)
        ErrorCounter.increment("unknown_transfer_contract", txid)


def handle_transfer_bridge_wormhole(exporter, elem, txinfo):
    wallet_address = txinfo.wallet_address
    txid = txinfo.txid
    COMMENT = "bridge wormhole"

    transfers_in, transfers_out = util_terra._transfers(elem, wallet_address, txid)

    if len(transfers_out) == 1 and len(transfers_in) == 0:
        sent_amount, sent_currency = transfers_out[0]
        row = make_transfer_out_tx(txinfo, sent_amount, sent_currency)
        row.comment = COMMENT
        exporter.ingest_row(row)
    elif len(transfers_in) == 1 and len(transfers_out) == 0:
        received_amount, received_currency = transfers_in[0]
        row = make_transfer_in_tx(txinfo, received_amount, received_currency)
        row.comment = COMMENT
        exporter.ingest_row(row)
    else:
        handle_unknown_detect_transfers(exporter, txinfo, elem)
