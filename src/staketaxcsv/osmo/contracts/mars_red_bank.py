

def handle_red_bank(exporter, txinfo, msginfo):
    msg = msginfo.execute_contract_message

    if "deposit" in msg:
        return _handle_deposit(exporter, txinfo, msginfo)

    raise Exception("Unable to handle tx in mars_red_bank.handle_red_bank()")


def _handle_deposit(exporter, txinfo, msginfo):
    transfers_in, transfers_out = msginfo.transfers
    raise Exception("Unable to handle tx in mars_red_bank._handle_deposit()")
