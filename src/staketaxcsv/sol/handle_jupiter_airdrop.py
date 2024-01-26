from staketaxcsv.sol.handle_simple import handle_unknown_detect_transfers
from staketaxcsv.common.make_tx import make_airdrop_tx


def handle_wen_airdrop(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers_net
    log_instructions = txinfo.log_instructions

    if len(transfers_in) == 1 and len(transfers_out) == 0 and "NewClaim" in log_instructions:
        received_amount, received_currency, _, _ = transfers_in[0]
        row = make_airdrop_tx(txinfo, received_amount, received_currency)
        exporter.ingest_row(row)
    else:
        handle_unknown_detect_transfers(exporter, txinfo)
