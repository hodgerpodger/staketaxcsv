from common.ExporterTypes import TX_TYPE_SOL_INIT_ACCOUNT
from common.make_tx import make_swap_tx
from sol.handle_simple import handle_unknown_detect_transfers
from sol.make_tx import make_lp_deposit_tx, make_lp_farm_tx, make_simple_tx


def handle_saber(exporter, txinfo):
    txinfo.comment = "saber_swap"
    log = txinfo.log

    transfers_in, transfers_out, transfers_unknown = txinfo.transfers_net

    if "Instruction: Swap" in log:
        if len(transfers_in) == 1 and len(transfers_out) == 1:
            received_amount, received_currency, _, _ = transfers_in[0]
            sent_amount, sent_currency, _, _ = transfers_out[0]

            row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
            exporter.ingest_row(row)
            return

    handle_unknown_detect_transfers(exporter, txinfo)


def handle_saber_stable_swap(exporter, txinfo):
    txinfo.comment = "saber_stable_swap"
    log_instructions = txinfo.log_instructions
    transfers_in, transfers_out, transfers_unknown = txinfo.transfers_net

    if "Deposit" in log_instructions and "MintTo" in log_instructions:
        if len(transfers_out) == 1 and len(transfers_in) == 1:
            received_amount, received_currency, _, _ = transfers_in[0]
            sent_amount, sent_currency, _, _ = transfers_out[0]

            row = make_lp_deposit_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
            exporter.ingest_row(row)
            return
        elif len(transfers_out) == 2 and len(transfers_in) == 1:
            for sent_amount, sent_currency, _, _ in transfers_out:
                row = make_lp_deposit_tx(txinfo, sent_amount, sent_currency, "", "", empty_fee=True)
                exporter.ingest_row(row)
            received_amount, received_currency, _, _ = transfers_in[0]
            row = make_lp_deposit_tx(txinfo, "", "", received_amount, received_currency, empty_fee=False)
            exporter.ingest_row(row)
            return

    handle_unknown_detect_transfers(exporter, txinfo)


def handle_saber_farm_ssf(exporter, txinfo):
    txinfo.comment = "saber_farm_ssf"
    transfers_in, transfers_out, transfers_unknown = txinfo.transfers_net

    if len(transfers_in) == 1 and len(transfers_out) == 0 and len(transfers_unknown) == 2:
        # lp farm (deposit lp token into farm)
        received_amount, received_currency, _, _ = transfers_in[0]

        for amount, currency, _, _ in transfers_unknown:
            if currency.startswith("2poo1"):
                row = make_lp_farm_tx(txinfo, amount, currency, received_amount, received_currency)
                exporter.ingest_row(row)
                return

    if (len(transfers_in) == 0 and len(transfers_out) == 0 and len(transfers_unknown) == 0
       and _is_init_account(txinfo)):
        # initialize account instructions only
        row = make_simple_tx(txinfo, TX_TYPE_SOL_INIT_ACCOUNT)
        exporter.ingest_row(row)
        return

    handle_unknown_detect_transfers(exporter, txinfo)


def _is_init_account(txinfo):
    """ Returns True if all log_instructions are "InitializeAccount" """
    log_instructions = txinfo.log_instructions

    if len(log_instructions) == 0:
        return False
    for log_instruction in log_instructions:
        if log_instruction != "InitializeAccount":
            return False

    return True
