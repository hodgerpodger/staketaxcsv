import logging
from datetime import datetime

import staketaxcsv.luna1.col4.handle
import staketaxcsv.luna1.col5.handle
import staketaxcsv.luna1.execute_type as ex
from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.common.ExporterTypes import TX_TYPE_GOV, TX_TYPE_LOTA_UNKNOWN, TX_TYPE_VOTE
from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.common.make_tx import make_spend_fee_tx
from staketaxcsv.luna1 import util_terra
from staketaxcsv.luna1.col4.handle_failed_tx import handle_failed_tx
from staketaxcsv.luna1.col4.handle_reward import handle_reward
from staketaxcsv.luna1.col4.handle_simple import handle_simple, handle_unknown, handle_unknown_detect_transfers
from staketaxcsv.luna1.col4.handle_swap import handle_swap_msgswap
from staketaxcsv.luna1.col4.handle_transfer import handle_ibc_transfer, handle_multi_transfer, handle_transfer
from staketaxcsv.luna1.config_luna1 import localconfig
from staketaxcsv.luna1.TxInfoTerra import MsgInfo, TxInfoTerra

# execute_type -> tx_type mapping for generic transactions with no tax details
EXECUTE_TYPES_SIMPLE = {
    ex.EXECUTE_TYPE_CAST_VOTE: TX_TYPE_VOTE,
    ex.EXECUTE_TYPE_REGISTER: TX_TYPE_LOTA_UNKNOWN,
}


def process_txs(wallet_address, elems, exporter, progress):
    for i, elem in enumerate(elems):
        process_tx(wallet_address, elem, exporter)

        if i % 50 == 0:
            progress.report(i + 1, "Processed {} of {} transactions".format(i + 1, len(elems)), "process_txs")


def process_tx(wallet_address, elem, exporter):
    txid = elem["txhash"]
    msgtype, txinfo = _txinfo(exporter, elem, wallet_address)

    if "code" in elem:
        # Failed transaction
        return handle_failed_tx(exporter, elem, txinfo)

    try:
        if msgtype == "bank/MsgSend":
            handle_transfer(exporter, elem, txinfo)
        elif msgtype == "bank/MsgMultiSend":
            handle_multi_transfer(exporter, elem, txinfo)
        elif msgtype == "cosmos-sdk/MsgTransfer":
            handle_ibc_transfer(exporter, elem, txinfo)
        elif msgtype == "ibc/MsgUpdateClient":
            handle_ibc_transfer(exporter, elem, txinfo)
        elif msgtype in ["gov/MsgVote", "gov/MsgDeposit", "gov/MsgSubmitProposal"]:
            handle_simple(exporter, txinfo, TX_TYPE_GOV)
        elif msgtype == "market/MsgSwap":
            handle_swap_msgswap(exporter, elem, txinfo)
        elif msgtype in ["staking/MsgDelegate", "distribution/MsgWithdrawDelegationReward",
                         "staking/MsgBeginRedelegate", "staking/MsgUndelegate"]:
            # LUNA staking reward
            handle_reward(exporter, elem, txinfo, msgtype)
        elif msgtype == "wasm/MsgExecuteContract":
            if staketaxcsv.luna1.col5.handle.can_handle(exporter, elem, txinfo):
                # THIS SHOULD BE FIRST CHOICE TO ADD NEW HANDLERS
                staketaxcsv.luna1.col5.handle.handle(exporter, elem, txinfo)
                logging.debug("Used col5 handler")
            else:
                # Legacy handlers
                staketaxcsv.luna1.col4.handle.handle(exporter, elem, txinfo)
                logging.debug("Used col4 handler")
        else:
            logging.error("Unknown msgtype for txid=%s", txid)
            ErrorCounter.increment("unknown_msgtype", txid)
            handle_unknown_detect_transfers(exporter, txinfo, elem)

    except Exception as e:
        logging.error("Exception when handling txid=%s, exception=%s", txid, str(e))
        ErrorCounter.increment("exception", txid)
        handle_unknown(exporter, txinfo)

        if localconfig.debug:
            raise (e)

    return txinfo


def _txinfo(exporter, elem, wallet_address):
    txid = elem["txhash"]
    timestamp = datetime.strptime(elem["timestamp"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
    fee, fee_currency, more_fees = _get_fee(elem)
    msgs = _msgs(elem, wallet_address)
    txinfo = TxInfoTerra(txid, timestamp, fee, fee_currency, wallet_address, msgs)
    msgtype = _get_first_msgtype(elem)

    # Handle transaction with multi-currency fee (treat as "spend" transactions)
    if more_fees:
        if msgtype == "bank/MsgSend" and elem["tx"]["value"]["msg"][0]["value"]["to_address"] == wallet_address:
            # This is a inbound transfer.  No fees
            pass
        else:
            for cur_fee, cur_currency in more_fees:
                row = make_spend_fee_tx(txinfo, cur_fee, cur_currency)
                row.comment = "multicurrency fee"
                exporter.ingest_row(row)

    return msgtype, txinfo


def _get_fee(elem):
    more_fees = []
    amounts = elem["tx"]["value"]["fee"]["amount"]

    # Handle special case for old transaction (16421CD60E56DA4F859088B7CA87BCF05A3B3C3F56CD4C0B2528EE0A797CC22D)
    if amounts is None or len(amounts) == 0:
        return 0, "", []

    # Parse fee element
    denom = amounts[0]["denom"]
    amount_string = amounts[0]["amount"]
    currency = util_terra._denom_to_currency(denom)
    fee = util_terra._float_amount(amount_string, currency)

    # Parse for tax info, add to fee if exists
    log = elem["logs"][0].get("log") if elem.get("logs") else None
    if log:
        tax_amount_string = log.get("tax", None)
        if tax_amount_string:
            tax_amount, tax_currency = util_terra._amount(tax_amount_string)
            if tax_currency == currency:
                fee += tax_amount
            else:
                more_fees.append((tax_amount, tax_currency))

    if len(amounts) == 1:
        # "normal" single fee

        # Special case for old col-3 transaction 7F3F1FA8AC89824B64715FEEE057273A873F240CA9A50BC4A87EEF4EE9813905
        if fee == 0:
            return 0, "", []
    else:
        # multi-currency fee
        for info in amounts[1:]:
            cur_denom = info["denom"]
            cur_amount_string = info["amount"]
            cur_currency = util_terra._denom_to_currency(cur_denom)
            cur_fee = util_terra._float_amount(cur_amount_string, cur_currency)

            more_fees.append((cur_fee, cur_currency))

    return fee, currency, more_fees


def _get_first_msgtype(elem):
    """Returns type identifier for this transaction"""
    return elem["tx"]["value"]["msg"][0]["type"]


def _msgs(elem, wallet_address):
    if "logs" not in elem:
        return []

    out = []
    for i in range(len(elem["logs"])):
        msg_type = elem["tx"]["value"]["msg"][i]["type"]
        log = elem["logs"][i]

        if msg_type == "wasm/MsgExecuteContract":
            execute_msg = util_terra._execute_msg(elem, i)
            transfers = util_terra._transfers_log(log, wallet_address)
            actions = _actions(log)
            contract = util_terra._contract(elem, i)
        else:
            execute_msg = None
            transfers = [[], []]
            actions = []
            contract = None

        msginfo = MsgInfo(i, execute_msg, transfers, log, actions, contract)
        out.append(msginfo)

    return out


def _actions(log):
    return MsgInfoIBC.wasm(log)
