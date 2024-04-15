from staketaxcsv.common.ibc.make_tx import make_spend_tx_fee


def is_vote(contract_data):
    return ("contract_info" in contract_data
            and contract_data["contract_info"].get("label") in (
                "neutron.proposals.single"))


def handle_vote(exporter, txinfo, msginfo):
    row = make_spend_tx_fee(txinfo, msginfo)
    row.comment = "vote"
    exporter.ingest_row(row)
