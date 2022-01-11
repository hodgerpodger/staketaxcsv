from common.make_tx import make_swap_tx
from sol import util_sol
from sol.handle_simple import handle_unknown
from sol.make_tx import make_lp_deposit_tx, make_lp_withdraw_tx


def handle_raydium_lp_v2(exporter, txinfo):
    txinfo.comment = "raydium_lp_v2"
    _handle_raydium_lp(exporter, txinfo)


def handle_raydium_lp_v3(exporter, txinfo):
    txinfo.comment = "raydium_lp_v3"
    _handle_raydium_lp(exporter, txinfo)


def handle_raydium_lp_v4(exporter, txinfo):
    txinfo.comment = "raydium_lp_v4"
    _handle_raydium_lp(exporter, txinfo)


def _handle_raydium_lp(exporter, txinfo):
    log_instructions = txinfo.log_instructions
    log_string = txinfo.log_string
    transfers_in, transfers_out, _ = txinfo.transfers_net

    if ("MintTo" in log_instructions
       and len(transfers_in) == 1
       and len(transfers_out) == 2):
        _handle_raydium_lp_deposit(exporter, txinfo, transfers_out)
    elif ("Burn" in log_instructions
          and len(transfers_in) == 2
          and len(transfers_out) == 1):
        _handle_raydium_lp_withdraw(exporter, txinfo, transfers_in, transfers_out)
    elif("process_swap:" in log_string
         and len(transfers_in) == 1
         and len(transfers_out) == 1):
        _handle_raydium_swap(exporter, txinfo, transfers_in, transfers_out)
    elif("process_swap_base_in:" in log_string
         and len(transfers_in) == 1
         and len(transfers_out) == 1):
        _handle_raydium_swap(exporter, txinfo, transfers_in, transfers_out)
    else:
        handle_unknown(exporter, txinfo)


def _handle_raydium_lp_deposit(exporter, txinfo, transfers_out):
    txid = txinfo.txid
    lp_info = txinfo.inner_parsed["mintTo"][0]

    # Get lp currency and amount
    mint = lp_info["mint"]
    amount_string = lp_info["amount"]
    lp_amount, lp_currency = util_sol.amount_currency(txinfo, amount_string, mint)

    # Create two LP_DEPOSIT rows
    i = 0
    for amount, currency, _, _ in transfers_out:
        row = make_lp_deposit_tx(txinfo, amount, currency, lp_amount / len(transfers_out), lp_currency, txid,
                                 empty_fee=(i > 0))
        exporter.ingest_row(row)
        i += 1


def _handle_raydium_lp_withdraw(exporter, txinfo, transfers_in, transfers_out):
    txid = txinfo.txid

    # Get lp currency and amount
    lp_amount, lp_currency, _, _ = transfers_out[0]

    # Create two LP_DEPOSIT rows
    i = 0
    for amount, currency, _, _ in transfers_in:
        row = make_lp_withdraw_tx(txinfo, amount, currency, lp_amount / len(transfers_in), lp_currency, txid,
                                  empty_fee=(i > 0))
        exporter.ingest_row(row)
        i += 1


def _handle_raydium_swap(exporter, txinfo, transfers_in, transfers_out):
    received_amount, received_currency, _, _ = transfers_in[0]
    sent_amount, sent_currency, _, _ = transfers_out[0]

    row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
    exporter.ingest_row(row)
