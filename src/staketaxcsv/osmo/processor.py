import logging

import staketaxcsv.common.ibc.processor
import staketaxcsv.osmo.handle_concentrated_lp
import staketaxcsv.osmo.handle_general
import staketaxcsv.osmo.handle_liquid
import staketaxcsv.osmo.handle_lp
import staketaxcsv.osmo.handle_staking
import staketaxcsv.osmo.handle_superfluid
import staketaxcsv.osmo.handle_swap
import staketaxcsv.osmo.handle_unknown
from staketaxcsv.osmo import constants as co
from staketaxcsv.osmo import util_osmo
from staketaxcsv.osmo.config_osmo import localconfig
from staketaxcsv.osmo.MsgInfoOsmo import MsgInfoOsmo
from staketaxcsv.settings_csv import OSMO_NODE
CONTRACT_LIQUID_STAKE = "osmo1f5vfcph2dvfeqcqkhetwv75fda69z7e5c2dldm3kvgj23crkv6wqcn47a0"


def process_txs(wallet_address, elems, exporter):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = staketaxcsv.common.ibc.processor.txinfo(
        wallet_address, elem, co.MINTSCAN_LABEL_OSMO, OSMO_NODE, MsgInfoOsmo)

    if txinfo.is_failed:
        staketaxcsv.common.ibc.processor.handle_failed_transaction(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        result = staketaxcsv.common.ibc.processor.handle_message(exporter, txinfo, msginfo, localconfig.debug)
        if result:
            continue

        _handle_message(exporter, txinfo, msginfo)

    return txinfo


def _handle_message(exporter, txinfo, msginfo):
    try:
        msg_type = util_osmo._msg_type(msginfo)

        # swaps
        if msg_type == co.MSG_TYPE_SWAP_IN:
            staketaxcsv.osmo.handle_swap.handle_swap(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_SPLIT_ROUTE_SWAP:
            staketaxcsv.osmo.handle_swap.handle_swap(exporter, txinfo, msginfo)

        # lp transactions
        elif msg_type == co.MSG_TYPE_JOIN_POOL:
            staketaxcsv.osmo.handle_lp.handle_lp_deposit(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_JOIN_SWAP_EXTERN_AMOUNT_IN:
            staketaxcsv.osmo.handle_lp.handle_lp_deposit_partial(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_EXIT_POOL:
            staketaxcsv.osmo.handle_lp.handle_lp_withdraw(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_LOCK_TOKENS:
            staketaxcsv.osmo.handle_lp.handle_lp_stake(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_BEGIN_UNLOCKING:
            staketaxcsv.osmo.handle_lp.handle_lp_unstake(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_UNLOCK_PERIOD_LOCK:
            staketaxcsv.osmo.handle_lp.handle_unlock_period_lock(exporter, txinfo, msginfo)

        # superfluid
        elif msg_type == co.MSG_TYPE_SUPERFLUID_DELEGATE:
            staketaxcsv.osmo.handle_superfluid.handle_delegate(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_LOCK_AND_SUPERFLUID_DELEGATE:
            staketaxcsv.osmo.handle_superfluid.handle_lp_stake(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_SUPERFLUID_UNDELEGATE, co.MSG_TYPE_SUPERFLUID_UNBOND_LOCK]:
            staketaxcsv.osmo.handle_superfluid.handle_undelegate_or_unbond(exporter, txinfo, msginfo)

        # concentrated liquidity
        elif msg_type == co.MSG_TYPE_CREATE_POSITION:
            staketaxcsv.osmo.handle_concentrated_lp.handle_create_position(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_ADD_TO_POSITION:
            staketaxcsv.osmo.handle_concentrated_lp.handle_add_to_position(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_COLLECT_INCENTIVES:
            staketaxcsv.osmo.handle_concentrated_lp.handle_collect_incentives(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_COLLECT_SPREAD_REWARDS:
            staketaxcsv.osmo.handle_concentrated_lp.handle_collect_spread_rewards(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_WITHDRAW_POSITION:
            staketaxcsv.osmo.handle_concentrated_lp.handle_withdraw_position(exporter, txinfo, msginfo)

        # execute contract
        elif msg_type == co.MSG_TYPE_EXECUTE_CONTRACT:
            _handle_execute_contract(exporter, txinfo, msginfo)

        else:
            staketaxcsv.osmo.handle_unknown.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
    except Exception as e:
        logging.error(
            "Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        staketaxcsv.osmo.handle_unknown.handle_unknown_detect_transfers(exporter, txinfo, msginfo)

        if localconfig.debug:
            raise e

    return txinfo


def _handle_execute_contract(exporter, txinfo, msginfo):
    contract = msginfo.contract

    if contract == CONTRACT_LIQUID_STAKE:
        staketaxcsv.osmo.handle_liquid.handle_liquid_stake(exporter, txinfo, msginfo)
    else:
        staketaxcsv.osmo.handle_unknown.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
