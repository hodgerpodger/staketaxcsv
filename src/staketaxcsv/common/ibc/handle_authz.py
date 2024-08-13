from staketaxcsv.common.ibc import make_tx, constants as co
from staketaxcsv.common.ibc.handle import handle_staking, handle_unknown


def handle_exec(exporter, txinfo, msginfo):
    # adjust fee to zero since wallet address in wrapped message does not pay fee
    # (address running exec message is fee payer)
    txinfo.fee = ""
    txinfo.fee_currency = ""

    if _is_exec_rpc_data(msginfo):
        _handle_exec_rpc_data(exporter, txinfo, msginfo)
    else:
        _handle_exec_lcd_data(exporter, txinfo, msginfo)


def handle_authz_grant(exporter, txinfo, msginfo):
    # handles grant message for authz

    if msginfo.msg_index == 0:
        row = make_tx.make_spend_tx_fee(txinfo, msginfo)
        exporter.ingest_row(row)
        row.comment = "spend fee for authz grant tx"


def handle_authz_revoke(exporter, txinfo, msginfo):
    # handles revoke message for authz

    if msginfo.msg_index == 0:
        row = make_tx.make_spend_tx_fee(txinfo, msginfo)
        exporter.ingest_row(row)
        row.comment = "spend fee for authz revoke tx"


def _is_exec_rpc_data(msginfo):
    message = msginfo.message

    if (
        msginfo.msg_type == co.MSG_TYPE_EXEC
        and message.get("@type", None) == "/cosmos.authz.v1beta1.MsgExec"
        and message.get("module", None) == "staking"
    ):
        return True
    else:
        return False


def _handle_exec_rpc_data(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    if len(transfers_in) == 0:
        pass
    else:
        handle_staking(exporter, txinfo, msginfo)


def _handle_exec_lcd_data(exporter, txinfo, msginfo):
    msg_types = set(map(lambda x: x["@type"].split(".")[-1], msginfo.message["msgs"]))

    # execs can have multiple messages, but the most common are to delegate and withdraw
    # if we can ensure our messages only contain those messages, we can reuse the staking handler
    if msg_types.issubset([co.MSG_TYPE_DELEGATE, co.MSG_TYPE_REDELEGATE, co.MSG_TYPE_WITHDRAW_REWARD,
                          co.MSG_TYPE_WITHDRAW_COMMISSION, co.MSG_TYPE_UNDELEGATE]):
        transfers_in, transfers_out = msginfo.transfers
        if len(transfers_in) == 0:
            # ignore delegatory messages not related to this wallet address to reduce verbosity
            pass
        else:
            handle_staking(exporter, txinfo, msginfo)
    elif msg_types.issubset([co.MSG_TYPE_LOCK_TOKENS]):
        owner = msginfo.message["msgs"][0]["owner"]
        if owner != exporter.wallet_address:
            # ignore lock token messages not related this wallet address
            pass
        else:
            # TODO: handle authz exec MsgLockTokens message
            handle_unknown(exporter, txinfo, msginfo)
    elif msg_types.issubset([co.MSG_TYPE_JOIN_SWAP_EXTERN_AMOUNT_IN]):
        sender = msginfo.message["msgs"][0]["sender"]
        if sender != exporter.wallet_address:
            # ignore lock token messages not related this wallet address
            pass
        else:
            # TODO: handle authz exec MsgJoinSwapExternAmountIn message
            handle_unknown(exporter, txinfo, msginfo)
    else:
        handle_unknown(exporter, txinfo, msginfo)
