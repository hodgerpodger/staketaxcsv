from terra.col5.contracts.config import CONTRACTS
from terra.constants import CUR_ASTRO
from terra import util_terra
from common.make_tx import make_airdrop_tx

CONTRACT_ASTROPORT_AIRDROP = "terra1dpe2aqykm2vnakcz4vgpha0agxnlkjvgfahhk7"


def handle_astroport_airdrop(elem, txinfo):
    txid = txinfo.txid

    for msg in txinfo.msgs:
        contract = msg.contract

        if contract == CONTRACT_ASTROPORT_AIRDROP:
            for action in msg.actions:
                if action["action"] == "Airdrop::ExecuteMsg::Claim":
                    amount_string = action["airdrop"]
                    currency = CUR_ASTRO
                    amount = util_terra._float_amount(amount_string, currency)

                    row = make_airdrop_tx(txinfo, amount, currency)
                    return [row]

    raise Exception("handle_astroport_airdrop(): Unable to handle txid={}".format(txid))


# Astroport Rewards Airdrop
CONTRACTS[CONTRACT_ASTROPORT_AIRDROP] = handle_astroport_airdrop
