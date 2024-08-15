from staketaxcsv.osmo.contracts.mars import extract_message


def handle_red_bank(exporter, txinfo, msginfo):
    msg = extract_message(msginfo)

    if "deposit" in msg:
        return _handle_deposit(exporter, txinfo, msginfo, msg)

    raise Exception("Unable to handle tx in mars_red_bank.handle_red_bank()")


def _handle_deposit(exporter, txinfo, msginfo, msg):
    transfers_in, transfers_out = msginfo.transfers
    raise Exception("Unable to handle tx in mars_red_bank._handle_deposit()")
