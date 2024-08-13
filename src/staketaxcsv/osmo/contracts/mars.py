from staketaxcsv.osmo.make_tx import make_osmo_reward_tx, make_osmo_simple_tx
from staketaxcsv.common.make_tx import make_spend_fee_tx


def handle_claim_rewards(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        received_amount, received_currency = transfers_in[0]

        row = make_osmo_reward_tx(txinfo, msginfo, received_amount, received_currency)
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in handle_mars.handle_claim_rewards()")


def handle_create_credit_account(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers

    if len(transfers_in) == 0 and len(transfers_out) == 0 and msginfo.msg_index == 0:
        row = make_spend_fee_tx(txinfo, txinfo.fee, txinfo.fee_currency)
        row.comment = "[mars create credit account]"
        exporter.ingest_row(row)
        return

    raise Exception("Unable to handle tx in handle_mars.handle_claim_rewards()")
