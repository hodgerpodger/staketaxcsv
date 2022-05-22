import common.ibc.handle
import common.ibc.processor
import dvpn.constants as co
from common.make_tx import make_spend_fee_tx, make_spend_tx
from dvpn.config_dvpn import localconfig
from settings_csv import DVPN_LCD_NODE


def process_txs(wallet_address, elems, exporter):
    for elem in elems:
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_DVPN, co.EXCHANGE_DVPN, localconfig.ibc_addresses, DVPN_LCD_NODE)

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
        _handle_management_message(exporter, txinfo, msginfo)
    elif msg_type in [co.MSG_TYPE_DVPN_SERVICE_SUBSCRIBE_TO_NODE, co.MSG_TYPE_DVPN_SERVICE_START,
                      co.MSG_TYPE_DVPN_SUBSCRIBE_TO_NODE_REQUEST, co.MSG_TYPE_DVPN_START_REQUEST, co.MSG_TYPE_DVPN_END_REQUEST]:
        # dVPN client subscription messages
        _handle_subscription_message(exporter, txinfo, msginfo)

    return False


def _handle_management_message(exporter, txinfo, msginfo):
    """
    Messages that update the status of a dVPN node on-chain which will have a fee.
    """
    _make_spend_fee_tx(exporter, txinfo, msginfo)


def _handle_subscription_message(exporter, txinfo, msginfo):
    """
    Messages that indicate what dVPN nodes a user has subscribed to and when a dVPN session starts.
    Pricing is maintained in message data.
    """
    msg_type = msginfo.msg_type
    if msg_type in [co.MSG_TYPE_DVPN_SERVICE_SUBSCRIBE_TO_NODE, co.MSG_TYPE_DVPN_SUBSCRIBE_TO_NODE_REQUEST]:
        _make_subscribed_to_node_tx(exporter, txinfo, msginfo)
    else:
        _make_spend_fee_tx(exporter, txinfo, msginfo)


def _make_subscribed_to_node_tx(exporter, txinfo, msginfo):
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


def _make_spend_fee_tx(exporter, txinfo, msginfo):
    row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)

    msg_type_for_comment = msginfo.msg_type.replace("Msg", "")
    row.comment = f"fee for {msg_type_for_comment}"

    exporter.ingest_row(row)
