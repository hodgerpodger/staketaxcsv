
from osmo.handle_unknown import handle_unknown_detect_transfers
from osmo.make_tx import make_osmo_swap_tx, make_osmo_reward_tx
from osmo import util_osmo


def handle_swap(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    # Preprocessing step to parse staking reward events first, if exists.
    _handle_claim(exporter, txinfo, msginfo)

    # Remove intermediate swap tokens (A -> B -> C; remove B)
    transfers_common = set(transfers_in).intersection(set(transfers_out))
    for t in transfers_common:
        transfers_in.remove(t)
        transfers_out.remove(t)

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        sent_amount, sent_currency = transfers_out[0]
        received_amount, received_currency = transfers_in[0]

        row = make_osmo_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo, msginfo)


def _handle_claim(exporter, txinfo, msginfo):
    """
    Parses message for "claim" event.
    If found, creates reward row and updates msginfo.transfers to remove reward inbound transfer
    """
    transfers_in, transfers_out = msginfo.transfers

    transfer_reward = _parse_claim_event(msginfo)
    if transfer_reward and transfer_reward in transfers_in:
        # Update msginfo.transfers
        transfers_in.remove(transfer_reward)

        # Create staking reward row
        reward_amount, reward_currency = transfer_reward
        row = make_osmo_reward_tx(txinfo, msginfo, reward_amount, reward_currency)
        exporter.ingest_row(row)


def _parse_claim_event(msginfo):
    """ Parses log for any "claim" event, which is a OSMO staking reward. """
    for event in msginfo.log["events"]:
        event_type = event["type"]
        if event_type == "claim":
            amount_string = event["attributes"][1]["value"]
            amount, currency = util_osmo._amount_currency(amount_string)[0]
            return (amount, currency)
    return None
