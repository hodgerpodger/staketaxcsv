from flipside import Flipside
import logging
from staketaxcsv.settings_csv import SOL_REWARDS_FLIPSIDE_API_KEY
from datetime import datetime
flipside = Flipside(SOL_REWARDS_FLIPSIDE_API_KEY, "https://api-v2.flipsidecrypto.xyz") if SOL_REWARDS_FLIPSIDE_API_KEY else None


def fetch_rewards_flipside(staking_address):
    """
    Fetch staking rewards for a specific address using Flipside Crypto API.
    """
    # Define SQL query
    sql = f"""
    SELECT
        BLOCK_TIMESTAMP,
        EPOCH_EARNED,
        REWARD_AMOUNT_SOL,
        POST_BALANCE_SOL
    FROM
        solana.gov.fact_rewards_staking
    WHERE
        STAKE_PUBKEY = '{staking_address}'
    ORDER BY
        BLOCK_TIMESTAMP ASC
    LIMIT 5000;
    """

    logging.info("Querying Flipside Crypto for staking rewards...")

    try:
        # Run the query
        query_result_set = flipside.query(sql)
        results = query_result_set.records

        # Format results (ignore `__row_index`)
        rewards = [
            (
                row["epoch_earned"],
                datetime.strptime(row["block_timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S"),
                row["reward_amount_sol"]
            )
            for row in results
        ]
        return rewards

    except Exception as e:
        logging.error(f"Failed to fetch rewards: {e}")
        return []
