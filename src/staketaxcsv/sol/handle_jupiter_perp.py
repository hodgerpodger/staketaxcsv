import logging
from staketaxcsv.sol.handle_simple import handle_unknown_detect_transfers
from staketaxcsv.common.make_tx import (
    make_perp_pnl_tx,
    make_transfer_out_tx,
    make_transfer_in_tx,
)

CUR_USD = "USD"


def handle_jupiter_perp(exporter, txinfo):
    txinfo.comment = "jupiter_perp"
    log_instructions = txinfo.log_instructions

    if _has_increase_position(log_instructions):
        txinfo.comment += ".increase_pos"
        _handle_increase_pos(exporter, txinfo)
    elif _has_decrease_position(log_instructions):
        txinfo.comment += ".decrease_pos"
        _handle_decrease_pos(exporter, txinfo)

    # important that "close position" is after increase/decrease
    elif _has_close_position(log_instructions):
        txinfo.comment += ".close_pos"
        _handle_close_pos(exporter, txinfo)

    else:
        logging.error("Unknown log_instructions")
        handle_unknown_detect_transfers(exporter, txinfo)


def _has_increase_position(log_instructions):
    for instruction in log_instructions:
        if "IncreasePosition" in instruction:
            return True
    return False


def _has_decrease_position(log_instructions):
    for instruction in log_instructions:
        if "DecreasePosition" in instruction:
            return True
    return False


def _has_close_position(log_instructions):
    for instruction in log_instructions:
        if "ClosePosition" in instruction:
            return True
    return False


def _verify_transfers_range(transfers_in, transfers_out, pos_type):
    # Ensure there is at least one transfer (in or out) and no more than 2 in either direction.
    if (len(transfers_in) == 0 and len(transfers_out) == 0) or (len(transfers_in) > 2 or len(transfers_out) > 2):
        raise Exception(f"Unable to handle jupiter perp {pos_type} pos: transfers out of expected range")


def _process_transfers(exporter, txinfo, transfers_in, transfers_out):
    # Process incoming transfers.
    for rec_amount, rec_cur, _, _ in transfers_in:
        row = make_transfer_in_tx(txinfo, rec_amount, rec_cur)
        row.comment += f"[received {rec_amount} {rec_cur}]"
        exporter.ingest_row(row)

    # Process outgoing transfers.
    for sent_amount, sent_cur, _, _ in transfers_out:
        row = make_transfer_out_tx(txinfo, sent_amount, sent_cur)
        row.comment += f"[sent {sent_amount} {sent_cur}]"
        exporter.ingest_row(row)


def _handle_increase_pos(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers
    _verify_transfers_range(transfers_in, transfers_out, "increase")
    _process_transfers(exporter, txinfo, transfers_in, transfers_out)


def _handle_close_pos(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers
    _verify_transfers_range(transfers_in, transfers_out, "close")
    _process_transfers(exporter, txinfo, transfers_in, transfers_out)


def _handle_decrease_pos(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers
    _verify_transfers_range(transfers_in, transfers_out, "decrease")
    _process_transfers(exporter, txinfo, transfers_in, transfers_out)

    # Process the realized pnl row.
    has_profit, pnl_delta = _parse_realized_pnl(txinfo.log)
    if has_profit is not None:
        row = make_perp_pnl_tx(txinfo, pnl_delta)
        row.comment += f"[pnl_delta={pnl_delta} USD]"
        exporter.ingest_row(row)
    else:
        logging.error("No pnl found")


def _parse_realized_pnl(log):
    """
    Expected log line format:
      "has_profit: true, pnl_delta: 2569308842"

    Returns:
      A tuple (has_profit, pnl_delta) where:
        - has_profit is a boolean indicating a gain (True) or a loss (False).
        - pnl_delta is a float representing the pnl in dollars (e.g., 2569.31).
      Returns (None, None) if parsing fails.
    """
    for entry in log:
        if "pnl_delta:" in entry:
            try:
                parts = entry.split(',')
                has_profit_str = parts[0].split("has_profit:")[1].strip()
                pnl_delta_str = parts[1].split("pnl_delta:")[1].strip()
                has_profit = has_profit_str.lower() == "true"
                pnl_delta = float(pnl_delta_str) / 1e6
                return has_profit, pnl_delta
            except Exception as e:
                logging.error("Error parsing realized pnl: %s", e)
                return None, None
    return None, None
