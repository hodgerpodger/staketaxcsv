
from staketaxcsv.common.ibc import make_tx, util_ibc
from staketaxcsv.strd import constants as co


def handle_claim_free_amount(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers_net
    events_by_type = msginfo.events_by_type
    txinfo.comment = "claim_free_amount "

    if len(transfers_in) > 0 and len(transfers_out) == 0:
        for amount, currency in util_ibc.aggregate_transfers(transfers_in):
            txinfo.comment += "[" + str(amount) + " " + currency + "]"

        raise Exception("Unable to determine consistently.  Treat as _UNKNOWN")

        # TODO: Find reliable way to determine if reward goes to wallet or claim-able area of wallet

        message = events_by_type["message"]
        if message.get("module") == "claim":
            # version where STRD reward goes to wallet directly
            for amount, currency in util_ibc.aggregate_transfers(transfers_in):
                row = make_tx.make_reward_tx(txinfo, msginfo, amount, currency)
                exporter.ingest_row(row)
        else:
            # version where STRD reward goes to reward-to-be-claimed part of wallet
            row = make_tx.make_simple_tx(txinfo, msginfo)
            exporter.ingest_row(row)

        return

    raise Exception("Unable to handle message in handle_claim_free_amount()")


def handle_liquid_stake(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    txinfo.comment += "liquid_stake"

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        received_amount, received_currency = transfers_in[0]
        sent_amount, sent_currency = transfers_out[0]

        row = make_tx.make_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
        return
    elif len(transfers_in) > 1 and len(transfers_out) == 1:
        net_transfers_in, net_transfers_out = util_ibc.aggregate_transfers_net(transfers_in, transfers_out)

        # Should be sum of: one STRD claim amount and liquid stake trade
        assert (len(net_transfers_in) == 2)
        assert (len(net_transfers_out) == 1)

        amt1, cur1 = net_transfers_in[0]
        amt2, cur2 = net_transfers_in[1]
        sent_amount, sent_currency = net_transfers_out[0]

        if cur1 == co.CURRENCY_STRD:
            claim_amount = amt1
            received_amount, received_currency = amt2, cur2
        elif cur2 == co.CURRENCY_STRD:
            claim_amount = amt2
            received_amount, received_currency = amt1, cur1
        else:
            raise Exception("Unexpected condition for cur1={}, cur2={}".format(cur1, cur2))

        row1 = make_tx.make_reward_tx(txinfo, msginfo, claim_amount, co.CURRENCY_STRD)
        row2 = make_tx.make_swap_tx(txinfo, msginfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row1)
        exporter.ingest_row(row2)
        return

    raise Exception("Unable to handle message in handle_liquid_stake()")
