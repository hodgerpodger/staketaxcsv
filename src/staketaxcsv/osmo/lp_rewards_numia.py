import logging

from staketaxcsv.osmo.api_numia import NumiaAPI
from staketaxcsv.osmo.make_tx import make_lp_reward_tx
from staketaxcsv.settings_csv import NUMIA_API_TOKEN, NUMIA_API_DOMAIN, OSMO_NODE
from staketaxcsv.osmo import denoms


def lp_rewards_tokens(wallet_address):
    """Fetch and return reward denominations for LP rewards."""
    if not NUMIA_API_TOKEN or not NUMIA_API_DOMAIN:
        logging.info("Missing numia token.  Not retrieving lp_rewards_tokens().")
        return []

    return NumiaAPI().get_reward_denoms(wallet_address)


def lp_rewards(wallet_address, exporter, progress):
    """Fetch and process LP rewards from Numia API and add rows to the exporter."""
    if not NUMIA_API_TOKEN or not NUMIA_API_DOMAIN:
        logging.info("Missing numia token.  Not retrieving lp_rewards().")
        return

    api = NumiaAPI()

    reward_denoms = api.get_reward_denoms(wallet_address)

    for i, denom in enumerate(reward_denoms):
        message = f"Retrieving LP rewards for denom={denom}"
        progress.report(i, message, "lp_rewards")

        rewards = api.get_rewards(wallet_address, denom)
        for reward in rewards:
            day = reward.get("timestamp")
            cl_amount_raw = reward.get("cl_amount")
            gamm_amount_raw = reward.get("gamm_amount")
            staking_amount_raw = reward.get("staking_amount")

            cl_amount, reward_currency = denoms.amount_currency_from_raw(cl_amount_raw, denom, OSMO_NODE)
            gamm_amount, _ = denoms.amount_currency_from_raw(gamm_amount_raw, denom, OSMO_NODE)
            staking_amount, _ = denoms.amount_currency_from_raw(staking_amount_raw, denom, OSMO_NODE)

            # Create rows only for non-zero rewards
            if cl_amount > 0:
                row = make_lp_reward_tx(wallet_address, day, cl_amount, reward_currency, row_comment="cl rewards")
                exporter.ingest_row(row)
            if gamm_amount > 0:
                row = make_lp_reward_tx(wallet_address, day, gamm_amount, reward_currency, row_comment="gamm rewards")
                exporter.ingest_row(row)
            if staking_amount > 0:
                row = make_lp_reward_tx(wallet_address, day, staking_amount, reward_currency, row_comment="staking rewards")
                exporter.ingest_row(row)
