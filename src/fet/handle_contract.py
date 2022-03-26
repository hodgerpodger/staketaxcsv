import common.ibc.handle
from common.ibc.MsgInfoIBC import MsgInfoIBC
from common.ibc import make_tx
import common.ibc.handle
import common.make_tx


CONTRACT_BRIDGE = "fetch18vd8fpwxzck93qlwghaj6arh4p7c5n890l3amr"


def handle_contract(exporter, txinfo):
    contract = txinfo.msgs[0].contract

    if contract == CONTRACT_BRIDGE:
        rows = _handle_bridge(exporter, txinfo)
    else:
        common.ibc.handle.handle_unknown_detect_transfers_tx(exporter, txinfo)
        return

    if rows:
        common.make_tx.ingest_rows(exporter, txinfo, rows)


def _handle_bridge(exporter, txinfo):
    if len(txinfo.msgs) != 1:
        common.ibc.handle.handle_unknown_detect_transfers_tx(exporter, txinfo)
        return

    msginfo = txinfo.msgs[0]
    transfers_in, transfers_out = msginfo.transfers
    wasm = msginfo.wasm

    # Prepare comment for bridge transaction
    bridge_url = "https://etherscan.io/tx/{}".format(wasm[0]["origin_tx_hash"].lower())
    comment = "bridge {}".format(bridge_url)

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        amount, currency = transfers_in[0]
        row = make_tx.make_transfer_in_tx(txinfo, msginfo, amount, currency)
        row.comment = comment
        return [row]
    elif len(transfers_in) == 0 and len(transfers_out) == 1:
        amount, currency = transfers_out[0]
        row = make_tx.make_transfer_out_tx(txinfo, msginfo, amount, currency)
        row.comment = comment
        return [row]
    else:
        common.ibc.handle.handle_unknown_detect_transfers(exporter, txinfo, msginfo)
        return []
