import staketaxcsv.common.make_tx

FIN_OWNER = "kujira1ghmq7k50rwpsnye39aefngd2k7x9kc2hrqq5xd"


def is_fin_contract(contract_history_data):
    return ("owner" in contract_history_data
           and contract_history_data["owner"] == FIN_OWNER)


def handle_fin(elem, txinfo):
    rows = []

    for msginfo in txinfo.msgs:
        actions = msginfo.wasm

        if _is_swap(actions):
            result = _handle_swap(txinfo, msginfo)
        else:
            raise Exception("handle_fin(): Unknown message.  actions={}".format(
                [action["action"] for action in actions]))

        rows.extend(result)
    return rows


def _is_swap(actions):
    action_names = [action["action"] for action in actions]

    return len(action_names) == 1 and action_names[0] == "swap"


def _handle_swap(txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        received_amount, received_currency = transfers_in[0]
        sent_amount, sent_currency = transfers_out[0]

        row = staketaxcsv.common.make_tx.make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        return [row]
    else:
        raise Exception("_handle_swap(): unable to handle transaction")
