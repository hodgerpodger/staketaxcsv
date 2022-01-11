from common.make_tx import make_swap_tx
from sol import constants as co
from sol.handle_simple import handle_unknown_detect_transfers

SOLANART = "solanart"
DIGITALEYES = "digitaleyes"
MAGICEDEN = "magiceden"
MAGICEDEN_MARKETPLACE = "magiceden_2"


def get_nft_program(txinfo):
    program_ids = txinfo.program_ids
    if co.PROGRAMID_SOLANART in program_ids:
        return SOLANART
    elif co.PROGRAMID_DIGITALEYES in program_ids:
        return DIGITALEYES
    elif co.PROGRAMID_MAGICEDEN in program_ids:
        return MAGICEDEN
    elif co.PROGRAMID_MAGICEDEN_MARKETPLACE in program_ids:
        return MAGICEDEN_MARKETPLACE
    else:
        return ""


def handle_nft_exchange(exporter, txinfo):
    transfers_in, transfers_out, transfers_unknown = txinfo.transfers_net
    nft_program = get_nft_program(txinfo)
    txinfo.comment = nft_program

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        # nft buy/sell
        received_amount, received_currency, _, _ = transfers_in[0]
        sent_amount, sent_currency, _, _ = transfers_out[0]
        if received_amount == 1 or sent_amount == 1:
            row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
            exporter.ingest_row(row)
            return

    if len(transfers_in) == 1 and len(transfers_out) == 0:
        # nft transfer out may not reflect in transfers.  Check nft transfer in transfers_unknown.
        nft_currency = _find_nft_currency(transfers_unknown)
        if nft_currency:
            received_amount, received_currency, _, _ = transfers_in[0]
            row = make_swap_tx(txinfo, 1, nft_currency, received_amount, received_currency)
            exporter.ingest_row(row)
            return

    handle_unknown_detect_transfers(exporter, txinfo)


def _find_nft_currency(transfers):
    for amount, currency, _, _ in transfers:
        if amount == 1:
            return currency
    return None
