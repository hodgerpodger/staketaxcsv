import logging
from staketaxcsv.sol.handle_simple import handle_unknown_detect_transfers
from staketaxcsv.common.make_tx import make_perp_pnl_tx, make_transfer_out_tx, make_transfer_in_tx

CREATE_INCREASE_POSITION_MARKET_REQUEST = "CreateIncreasePositionMarketRequest"
CREATE_DECREASE_POSITION_MARKET_REQUEST = "CreateDecreasePositionMarketRequest"
DECREASE_POSITION_4 = "DecreasePosition4"
CUR_USD = "USD"


def handle_jupiter_perp(exporter, txinfo):
    txinfo.comment = "jupiter_perp"
    transfers_in, transfers_out, _ = txinfo.transfers_net
    log_instructions = txinfo.log_instructions

    if CREATE_INCREASE_POSITION_MARKET_REQUEST in log_instructions:
        txinfo.comment += ".increase_pos"
        _handle_increase_pos(exporter, txinfo)
    elif CREATE_DECREASE_POSITION_MARKET_REQUEST in log_instructions or DECREASE_POSITION_4 in log_instructions:
        txinfo.comment += ".decrease_pos"
        _handle_decrease_pos(exporter, txinfo)
    else:
        logging.error("Unknown log_instructions")
        handle_unknown_detect_transfers(exporter, txinfo)


def _handle_increase_pos(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers_net
    if len(transfers_out) == 1 and len(transfers_in) == 0:
        sent_amount, sent_cur, _, _ = transfers_out[0]

        # jup perp increase pos: treat as transfer out tx
        row = make_transfer_out_tx(txinfo, sent_amount, sent_cur)
        row.comment += f"[deposit {sent_amount} {sent_cur}]"
        exporter.ingest_row(row)

        return

    raise Exception("Unable to handle jupiter perp increase pos in _handle_increase_pos()")


def _handle_decrease_pos(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers_net
    if len(transfers_in) == 1 and not transfers_out:
        rec_amount, rec_cur, _, _ = transfers_in[0]

        # jup perp decrease pos: treat as 2 txs
        # - transfer in tx
        # - realize pnl row

        # transfer in tx
        row = make_transfer_in_tx(txinfo, rec_amount, rec_cur)
        row.comment += f"[withdraw {rec_amount} {rec_cur}]"
        exporter.ingest_row(row)

        # realize pnl row
        has_profit, pnl_delta = _parse_realized_pnl(txinfo.log)
        if has_profit is not None:
            row = make_perp_pnl_tx(txinfo, pnl_delta)
            row.comment += f"[pnl_delta={pnl_delta} USD]"
            exporter.ingest_row(row)
            return
        else:
            logging.error("Realized pnl not found in log")

    raise Exception("Unable to handle jupiter perp decrease pos in _handle_decrease_pos()")


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
