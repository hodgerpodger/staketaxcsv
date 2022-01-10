from osmo import util_osmo
from osmo.make_tx import make_osmo_reward_tx


def handle_claim(exporter, txinfo, msginfo):
    """
    Helper function to parse message for "claim" event.
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
