from staketaxcsv.inj import constants as co
from staketaxcsv.common.ibc import make_tx


def handle_send_to_eth(exporter, txinfo, msginfo):
    message = msginfo.message

    eth_dest = message["eth_dest"]

    # Get amount INJ sent to eth bridge
    sent_amount_raw, sent_currency_raw = message["amount"]["amount"], message["amount"]["denom"]
    assert (sent_currency_raw == "inj")
    sent_amount = float(sent_amount_raw) / co.EXP_18

    # Get bridge fee
    bridge_fee_amount_raw, bridge_fee_currency_raw = message["bridge_fee"]["amount"], message["bridge_fee"]["denom"]
    assert (bridge_fee_currency_raw == "inj")
    bridge_fee_amount = float(bridge_fee_amount_raw) / co.EXP_18

    txinfo.fee += bridge_fee_amount
    row = make_tx.make_transfer_out_tx(txinfo, msginfo, sent_amount, co.CURRENCY_INJ)
    row.comment += f"send to eth bridge [eth_dest={eth_dest}]"
    exporter.ingest_row(row)
