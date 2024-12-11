import logging
from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC


def is_authz_no_logs_tx(elem):
    """
    Checks if logs are missing and the first message is MsgExec.
    """
    if not elem.get("logs"):
        messages = elem.get("tx", {}).get("body", {}).get("messages", [])
        if len(messages) == 0:
            return False

        first_message = messages[0]
        if first_message.get("@type") == "/cosmos.authz.v1beta1.MsgExec":
            return True

    return False


def handle_authz_no_logs_tx(wallet_address, elem, lcd_node):
    """
    Handles transactions with missing 'logs' by using the 'events' element.
    Returns a list of MsgInfoIBC objects.
    """
    txid = elem["txhash"]
    logging.warning(f"Missing 'logs' for transaction {txid}. Falling back to 'events'.")

    # Group events by their 'msg_index' for efficient processing
    events_by_msg_index = _group_events_by_msg_index(elem.get("events", []))

    msgs = []

    # Process each top-level message
    for i, message in enumerate(elem["tx"]["body"]["messages"]):
        associated_events = events_by_msg_index.get(i, [])
        if message["@type"] == "/cosmos.authz.v1beta1.MsgExec":
            # Special handling for MsgExec, further processing sub-messages
            msgs.extend(
                _process_msgexec(wallet_address, message, lcd_node, associated_events)
            )
        else:
            raise Exception(f"Unexpected message type '{message['@type']}' for transaction {txid}")

    return msgs


def _group_events_by_msg_index(events):
    """
    Groups events by their 'msg_index' field.
    """
    grouped_events = {}
    for event in events:
        for attribute in event.get("attributes", []):
            if attribute["key"] == "msg_index":
                try:
                    msg_index = int(attribute["value"])
                    if msg_index not in grouped_events:
                        grouped_events[msg_index] = []
                    grouped_events[msg_index].append(event)
                except ValueError:
                    logging.error(f"Invalid msg_index value in event: {attribute}")
    return grouped_events


def _process_msgexec(wallet_address, message, lcd_node, parent_events):
    """
    Handles MsgExec messages by extracting sub-messages and returning them as MsgInfoIBC objects.
    Groups events for sub-messages by 'authz_msg_index'.
    """
    sub_msgs = []

    # Group parent events by 'authz_msg_index' for sub-message association
    events_by_authz_index = _group_events_by_authz_msg_index(parent_events)

    sub_messages = message.get("msgs", [])
    for sub_msg_index, sub_message in enumerate(sub_messages):
        associated_events = events_by_authz_index.get(sub_msg_index, [])
        # Filter out messages/events not related to the wallet address
        if not _is_relevant_to_wallet(wallet_address, associated_events):
            continue

        sub_msginfo = MsgInfoIBC(wallet_address, sub_msg_index, sub_message, None, lcd_node, events=associated_events)
        sub_msgs.append(sub_msginfo)

    return sub_msgs


def _group_events_by_authz_msg_index(events):
    """
    Groups events by their 'authz_msg_index' field for MsgExec sub-messages.
    """
    grouped_events = {}
    for event in events:
        for attribute in event.get("attributes", []):
            if attribute["key"] == "authz_msg_index":
                try:
                    authz_msg_index = int(attribute["value"])
                    if authz_msg_index not in grouped_events:
                        grouped_events[authz_msg_index] = []
                    grouped_events[authz_msg_index].append(event)
                except ValueError:
                    logging.error(f"Invalid authz_msg_index value in event: {attribute}")
    return grouped_events


def _is_relevant_to_wallet(wallet_address, events):
    """
    Determines if the given events are relevant to the specified wallet address.
    Checks sender, recipient, or any wallet-specific keys in the attributes.
    """
    for event in events:
        for attribute in event.get("attributes", []):
            if attribute["value"] == wallet_address:
                return True
    return False
