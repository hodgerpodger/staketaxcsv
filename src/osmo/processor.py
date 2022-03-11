import logging
from datetime import datetime

from osmo import constants as co
from osmo import util_osmo
from osmo.config_osmo import localconfig
from osmo.TxInfoOsmo import MsgInfo, TxInfoOsmo
import osmo.handle_general
import osmo.handle_lp
import osmo.handle_swap
import osmo.handle_staking
import osmo.handle_unknown
import osmo.handle_superfluid


def process_txs(wallet_address, elems, exporter):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)


def process_tx(wallet_address, elem, exporter):
    txinfo = _parse_tx(elem, wallet_address)

    # Detect failed transaction
    if elem["code"] > 0:
        osmo.handle_general.handle_failed_tx(exporter, txinfo)
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
            osmo.handle_general.handle_simple(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_SUBMIT_PROPOSAL:
            transfers_in, transfers_out = msginfo.transfers
            if len(transfers_in) == 0 and len(transfers_out) == 1:
                osmo.handle_general.handle_simple_outbound(exporter, txinfo, msginfo)
            else:
                osmo.handle_general.handle_simple(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_DEPOSIT]:
            # 1 outbound transfer
            osmo.handle_general.handle_simple_outbound(exporter, txinfo, msginfo)
        elif msg_type in [co.MSG_TYPE_UPDATE_CLIENT, co.MSG_TYPE_ACKNOWLEDGMENT]:
            pass

        # staking rewards
        elif msg_type in [co.MSG_TYPE_DELEGATE, co.MSG_TYPE_REDELEGATE, co.MSG_TYPE_WITHDRAW_REWARD,
                          co.MSG_TYPE_WITHDRAW_COMMISSION, co.MSG_TYPE_UNDELEGATE]:
            osmo.handle_staking.handle_staking(exporter, txinfo, msginfo)

        # transfers
        elif msg_type in [co.MSG_TYPE_IBC_TRANSFER, co.MSG_TYPE_MSGRECVPACKET]:
            osmo.handle_general.handle_transfer_ibc(exporter, txinfo, msginfo)
        elif msg_type == co.MSG_TYPE_TIMEOUT:
            # ibc transfer timeout
            pass
        elif msg_type == co.MSG_TYPE_SEND:
            osmo.handle_general.handle_transfer(exporter, txinfo, msginfo)

        # swaps
        elif msg_type == co.MSG_TYPE_SWAP_IN:
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
