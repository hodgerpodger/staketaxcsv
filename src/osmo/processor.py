import logging
from datetime import datetime

from osmo import constants as co
from osmo import util_osmo
from osmo.config_osmo import localconfig
from osmo.handle_general import (
    handle_failed_tx,
    handle_simple,
    handle_simple_outbound,
    handle_transfer,
    handle_transfer_ibc,
)
from osmo.handle_lp import (
    handle_lp_deposit,
    handle_lp_deposit_partial,
    handle_lp_stake,
    handle_lp_unstake,
    handle_lp_withdraw,
)
from osmo.handle_staking import handle_staking
from osmo.handle_swap import handle_swap
from osmo.handle_unknown import handle_unknown_detect_transfers
from osmo.TxInfoOsmo import MsgInfo, TxInfoOsmo


def process_txs(wallet_address, elems, exporter):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = _parse_tx(elem, wallet_address)

    # Detect failed transaction
    if elem["code"] > 0:
        handle_failed_tx(exporter, txinfo)
        return txinfo

    for msginfo in txinfo.msgs:
        _handle_message(exporter, txinfo, msginfo)

    return txinfo


def _handle_message(exporter, txinfo, msginfo):
    try:
        msg_type = util_osmo._msg_type(msginfo)

        # simple transactions, that are typically ignored
        if msg_type in [co.MSG_TYPE_VOTE, co.MSG_TYPE_SET_WITHDRAW_ADDRESS]:
            # 0 transfers
            handle_simple(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_SUBMIT_PROPOSAL, co.MSG_TYPE_DEPOSIT]:
            # 1 outbound transfer
            handle_simple_outbound(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_UPDATE_CLIENT, co.MSG_TYPE_ACKNOWLEDGMENT]:
            pass

        # staking rewards
        elif msg_type in [co.MSG_TYPE_DELEGATE, co.MSG_TYPE_REDELEGATE, co.MSG_TYPE_WITHDRAW_REWARD,
                          co.MSG_TYPE_WITHDRAW_COMMISSION, co.MSG_TYPE_UNDELEGATE]:
            handle_staking(exporter, txinfo, msginfo)

        # transfers
        elif msg_type in [co.MSG_TYPE_IBC_TRANSFER, co.MSG_TYPE_MSGRECVPACKET]:
            handle_transfer_ibc(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_TIMEOUT:
            # ibc transfer timeout
            pass
        elif msg_type == co.MSG_TYPE_SEND:
            handle_transfer(exporter, txinfo, msginfo)

        # swaps
        elif msg_type == co.MSG_TYPE_SWAP_IN:
            handle_swap(exporter, txinfo, msginfo)

        # lp transactions
        elif msg_type == co.MSG_TYPE_JOIN_POOL:
            handle_lp_deposit(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_JOIN_SWAP_EXTERN_AMOUNT_IN:
            handle_lp_deposit_partial(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_EXIT_POOL:
            handle_lp_withdraw(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_LOCK_TOKENS:
            handle_lp_stake(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_BEGIN_UNLOCKING:
            handle_lp_unstake(exporter, txinfo, msginfo)
        else:
            handle_unknown_detect_transfers(exporter, txinfo, msginfo)
    except Exception as e:
        logging.error(
            "Exception when handling txid=%s, exception=%s", txinfo.txid, str(e))
        handle_unknown_detect_transfers(exporter, txinfo, msginfo)

        if localconfig.debug:
            raise(e)

    return txinfo


def _parse_tx(elem, wallet_address):
    txid = elem["txhash"]
    timestamp = datetime.strptime(
        elem["timestamp"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
    fee, fee_currency = _fee(elem)

    # Construct list of MsgInfo's
    msgs = []
    for i in range(len(elem["logs"])):
        message = elem["tx"]["body"]["messages"][i]
        log = elem["logs"][i]
        transfers = util_osmo._transfers(log, wallet_address)

        msginfo = MsgInfo(message, transfers, i, log)
        msgs.append(msginfo)

    txinfo = TxInfoOsmo(txid, timestamp, fee, wallet_address, msgs)
    return txinfo


def _fee(elem):
    fees = elem["tx"]["auth_info"]["fee"]["amount"]
    if len(fees) == 0:
        return "", ""

    first_fee = fees[0]
    fee_amount = float(first_fee["amount"]) / co.MILLION
    fee_currency = co.CUR_OSMO

    if not fee_amount:
        return "", ""
    return fee_amount, fee_currency
