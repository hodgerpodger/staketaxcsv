import requests
import logging
import csv
from io import StringIO
from datetime import datetime, timezone
from staketaxcsv.settings_csv import SOL_REWARDS_SOLSCAN_API_TOKEN


def fetch_rewards_solscan(staking_address):
    """
    Fetch staking rewards for a specific address using Solscan Pro API.
    """
    # Define API endpoint and headers
    API_URL = "https://pro-api.solscan.io/v2.0/account/reward/export"

    headers = {
        "token": SOL_REWARDS_SOLSCAN_API_TOKEN,
    }

    # Define query parameters
    time_from = int(datetime(2018, 1, 1, tzinfo=timezone.utc).timestamp())
    time_to = int(datetime.now(tz=timezone.utc).timestamp())

    params = {
        "address": staking_address,
        "time_from": time_from,
        "time_to": time_to,
    }

    logging.info(f"Querying Solscan Pro API at {API_URL} with params: {params}")

    # Make the API request
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        # If a 400 error is returned (e.g., malformed/non-existent address),
        # we want to return an empty list instead of raising an exception.
        if response.status_code == 400:
            logging.warning(
                f"Received 400 error from Solscan for address '{staking_address}'. "
                "Likely malformed or non-existent. Returning empty list."
            )
            return []
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # If some other HTTP error occurs, you can either re-raise or handle differently
        logging.error(f"HTTP error encountered: {e}")
        raise
    csv_data = response.text

    # Parse CSV output using csv module
    csv_reader = csv.reader(StringIO(csv_data))
    rewards = []

    # Skip the header row
    header = next(csv_reader, None)  # Skip header row
    if header is None:
        logging.warning("CSV data is empty or malformed.")
        return rewards  # Return an empty list if no data is present

    # Process each row
    for row in csv_reader:
        if len(row) < 5:  # Ensure the row has enough columns
            logging.info(f"Skipping row: {row}")
            continue
        elif row[0].strip() == "Epoch":
            # skip header row
            continue
        try:
            epoch = int(row[0].strip())
            effective_time_unix = int(row[2].strip())  # Parse effective time as Unix timestamp
            effective_time = datetime.utcfromtimestamp(effective_time_unix).strftime("%Y-%m-%d %H:%M:%S")
            reward_amount = float(row[4].strip())  # Parse reward amount

            rewards.append((epoch, effective_time, reward_amount))
        except (ValueError, IndexError) as e:
            logging.error(f"Error processing row {row}: {e}")
            continue

    # Sort rewards by effective_time_unix (chronological order)
    rewards.sort(key=lambda x: datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S"))

    # Remove exact duplicates. If you only want to key by epoch alone, adapt accordingly.
    unique_rewards = []
    seen = set()
    for r in rewards:
        if r not in seen:
            unique_rewards.append(r)
            seen.add(r)

    return unique_rewards
