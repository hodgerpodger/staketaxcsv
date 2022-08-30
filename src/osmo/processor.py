import logging

from osmo import constants as co
from osmo import util_osmo
from osmo.config_osmo import localconfig
from osmo.MsgInfoOsmo import MsgInfoOsmo
import osmo.handle_general
import osmo.handle_lp
import osmo.handle_swap
import osmo.handle_staking
import osmo.handle_unknown
import osmo.handle_superfluid
import common.ibc.processor
from settings_csv import OSMO_NODE


def process_txs(wallet_address, elems, exporter):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_OSMO, localconfig.ibc_addresses, OSMO_NODE, MsgInfoOsmo)

    # Detect failed transaction
    if elem["code"] > 0:
        osmo.handle_general.handle_failed_tx(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        result = common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        _handle_message(exporter, txinfo, msginfo)

    return txinfo


def _handle_message(exporter, txinfo, msginfo):
    try:
        msg_type = util_osmo._msg_type(msginfo)

        # swaps
        if msg_type == co.MSG_TYPE_SWAP_IN:
            osmo.handle_swap.handle_swap(exporter, txinfo, msginfo)

        # lp transactions
        elif msg_type == co.MSG_TYPE_JOIN_POOL:
            osmo.handle_lp.handle_lp_deposit(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_JOIN_SWAP_EXTERN_AMOUNT_IN:
            osmo.handle_lp.handle_lp_deposit_partial(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_EXIT_POOL:
            osmo.handle_lp.handle_lp_withdraw(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_LOCK_TOKENS:
            osmo.handle_lp.handle_lp_stake(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_BEGIN_UNLOCKING:
            osmo.handle_lp.handle_lp_unstake(exporter, txinfo, msginfo)

        # superfluid
        elif msg_type == co.MSG_TYPE_SUPERFLUID_DELEGATE:
            osmo.handle_superfluid.handle_delegate(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_LOCK_AND_SUPERFLUID_DELEGATE:
            osmo.handle_superfluid.handle_lp_stake(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_SUPERFLUID_UNDELEGATE, co.MSG_TYPE_SUPERFLUID_UNBOND_LOCK]:
            osmo.handle_superfluid.handle_undelegate_or_unbond(exporter, txinfo, msginfo)

        else:
            osmo.handle_unknown.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
    except Exception as e:
        logging.error(
            "Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        osmo.handle_unknown.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

        if localconfig.debug:
            raise e

    return txinfo
