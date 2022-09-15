
import staketaxcsv.common.ibc.handle
import staketaxcsv.fet.fetchhub1.constants as co2
from staketaxcsv.common.ibc import make_tx
from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.common.make_tx import ingest_rows, make_spend_fee_tx


def handle_tx(exporter, txinfo):
    rows = []

    for msginfo in txinfo.msgs:
        msg_type = msginfo.msg_type

        # non-monetary tx, with fee usually
        if msg_type in (co2.ACTION_TYPE_VOTE):
            result = _handle_simple(exporter, txinfo, msginfo)

        # staking rewards
        elif msg_type in (co2.ACTION_TYPE_DELEGATE, co2.ACTION_TYPE_WITHDRAW_DELEGATOR_REWARD,
                          co2.ACTION_TYPE_UNDELEGATE, co2.ACTION_TYPE_WITHDRAW_VALIDATOR_COMMISSION,
                          co2.ACTION_TYPE_REDELEGATE):
            result = _handle_staking(exporter, txinfo, msginfo)

        # transfers
        elif msg_type == co2.ACTION_TYPE_SEND:
            result = _handle_transfer(exporter, txinfo, msginfo)

        else:
            common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
            result = None

        if result:
            rows.extend(result)

    ingest_rows(exporter, txinfo, rows)


def _handle_simple(exporter, txinfo, msginfo):

    if txinfo.fee and msginfo.msg_index == 0:
        # Make a spend fee csv row
        row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)
        row.comment = "fee for {}".format(msginfo.msg_type)
    else:
        # Make a custom tx for info purposes only; doesn't affect ledger
        row = make_tx.make_simple_tx(txinfo, msginfo)
    return [row]


def _handle_transfer(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        amount, currency = transfers_in[0]
        row = make_tx.make_transfer_in_tx(txinfo, msginfo, amount, currency)
        return [row]
    elif len(transfers_in) == 0 and len(transfers_out) == 1:
        amount, currency = transfers_out[0]
        row = make_tx.make_transfer_out_tx(txinfo, msginfo, amount, currency)
        return [row]
    else:
        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
        return []


def _handle_staking(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    total = 0
    for amount, currency in transfers_in:
        total += amount

    if total > 0:
        row = make_tx.make_reward_tx(txinfo, msginfo, total, currency)
        row.comment = "claim reward in {}".format(msginfo.msg_type)
        return [row]
    else:
        # No reward: add non-income delegation transaction just so transaction doesn't appear "missing"
        row = make_tx.make_simple_tx(txinfo, msginfo)
        return [row]
