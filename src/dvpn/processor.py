import staketaxcsv.common.ibc.handle
import staketaxcsv.common.ibc.processor
import staketaxcsv.dvpn.constants as co
from staketaxcsv.common.make_tx import make_spend_fee_tx, make_spend_tx
from staketaxcsv.dvpn.config_dvpn import localconfig
from staketaxcsv.settings_csv import DVPN_LCD_NODE

_handled_fee_spend_tx_hashes = set()


def process_usage_payments(wallet_address, exporter):
    """
    Uses the sentinelhub API to calculate usage payments from escrow to the node operator.
    As this data is held off-chain, the algorithm will need to leverage sentinelhub APIs to:
        1. Get all subscriptions for the sentnode1 address (currently, this is not indexed by the sentnode1 address and requires a brute force search across all subscriptions)
        2. For each subscription the node has, get the current usage from the quota
        3. Multiply the usage percentage by the price set in the subscription

    Also, need to figure out what timestamp can be used with the payment.
    Quotas, unfortunately, do not contain a timestamp.
    Subscriptions have a timestamp corresponding to the last status update time which might be the best we can do.

    As there isn't indexing by sentinel node and only the latest data is provided by the quotas and subscription
    APIs instead of a time series, this implementation is still TODO.
    TODO: finish this implementation
    """
    pass


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_DVPN, localconfig.ibc_addresses, DVPN_LCD_NODE)

    for msginfo in txinfo.msgs:
        # Handle sentinel specific messages
        result = _handle_tx(exporter, txinfo, msginfo)
        if result:
            continue

        # Handle common messages
        result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        # Handle unknown messages
        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

    return txinfo


def _handle_tx(exporter, txinfo, msginfo):
    """
    Handles sentinel specific transactions.
    """

    msg_type = msginfo.msg_type
    if msg_type in [co.MSG_TYPE_DVPN_REGISTER_REQUEST, co.MSG_TYPE_DVPN_SET_STATUS_REQUEST,
                    co.MSG_TYPE_DVPN_UPDATE_REQUEST]:
        # dVPN node management messages
        _handle_management_tx(exporter, txinfo, msginfo)
    elif msg_type in [co.MSG_TYPE_DVPN_SERVICE_SUBSCRIBE_TO_NODE, co.MSG_TYPE_DVPN_SERVICE_START, co.MSG_TYPE_DVPN_SERVICE_END,
                      co.MSG_TYPE_DVPN_SUBSCRIBE_TO_NODE_REQUEST, co.MSG_TYPE_DVPN_START_REQUEST, co.MSG_TYPE_DVPN_END_REQUEST]:
        # dVPN client subscription messages
        _handle_subscription_tx(exporter, txinfo, msginfo)
    else:
        return False

    return True


def _handle_management_tx(exporter, txinfo, msginfo):
    """
    Messages that update the status of a dVPN node on-chain which will have a fee.
    """
    _handle_spend_fee_tx(exporter, txinfo, msginfo)


def _handle_subscription_tx(exporter, txinfo, msginfo):
    """
    Messages that indicate what dVPN nodes a user has subscribed to and when a dVPN session starts.
    Pricing is maintained in message data.
    """
    msg_type = msginfo.msg_type
    if msg_type in [co.MSG_TYPE_DVPN_SERVICE_SUBSCRIBE_TO_NODE, co.MSG_TYPE_DVPN_SUBSCRIBE_TO_NODE_REQUEST]:
        _handle_subscribed_to_node_tx(exporter, txinfo, msginfo)
    else:
        _handle_spend_fee_tx(exporter, txinfo, msginfo)


def _handle_spend_fee_tx(exporter, txinfo, msginfo):
    global _handled_fee_spend_tx_hashes

    # transactions can have multiple messages and the fee should only count once
    if txinfo.txid in _handled_fee_spend_tx_hashes:
        return

    _handled_fee_spend_tx_hashes.add(txinfo.txid)

    row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)

    msg_type_for_comment = msginfo.msg_type.replace("Msg", "")
    row.comment = f"fee for {msg_type_for_comment}"

    exporter.ingest_row(row)


def _handle_subscribed_to_node_tx(exporter, txinfo, msginfo):
    _, transfers_out = msginfo.transfers
    assert len(transfers_out) == 1

    sent_amount, sent_currency = transfers_out[0]
    row = make_spend_tx(txinfo, sent_amount, sent_currency)

    comment = "subscribed to dVPN node"
    dvpn_node_address = msginfo.message.get("address")
    if dvpn_node_address:
        comment = f"{comment}: {dvpn_node_address}"
    row.comment = comment

    exporter.ingest_row(row)
