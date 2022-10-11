import staketaxcsv.common.ibc.handle
import staketaxcsv.common.make_tx
from staketaxcsv.common.ibc import make_tx
from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC

CONTRACT_BRIDGE_V1 = "fetch18vd8fpwxzck93qlwghaj6arh4p7c5n890l3amr"
CONTRACT_BRIDGE_V2 = "fetch1qxxlalvsdjd07p07y3rc5fu6ll8k4tmetpha8n"


def handle_contract(exporter, txinfo):
    contract = txinfo.msgs[0].contract

    if contract in [CONTRACT_BRIDGE_V1, CONTRACT_BRIDGE_V2]:
        rows = _handle_bridge_transfer_v1(exporter, txinfo)
    else:
        common.ibc.handle.handle_unknown_detect_transfers_tx(exporter, txinfo)
        return

    if rows:
        common.make_tx.ingest_rows(exporter, txinfo, rows)


def _handle_bridge_transfer_v1(exporter, txinfo):
    if len(txinfo.msgs) != 1:
        common.ibc.handle.handle_unknown_detect_transfers_tx(exporter, txinfo)
        return

    msginfo = txinfo.msgs[0]
    transfers_in, transfers_out = msginfo.transfers
    wasm = msginfo.wasm

    # Prepare comment for bridge transaction
    comment = "bridge"
    if wasm and "origin_tx_hash" in wasm[0]:
        bridge_url = "https://etherscan.io/tx/{}".format(wasm[0]["origin_tx_hash"].lower())
        comment += " {}".format(bridge_url)

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        amount, currency = transfers_in[0]
        row = make_tx.make_transfer_in_tx(txinfo, msginfo, amount, currency)
        row.comment = comment
        return [row]
    elif len(transfers_out) == 1 and len(transfers_in) == 0:
        amount, currency = transfers_out[0]
        row = make_tx.make_transfer_out_tx(txinfo, msginfo, amount, currency)
        row.comment = comment
        return [row]
    else:
        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
        return []
