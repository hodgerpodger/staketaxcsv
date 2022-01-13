import os

# Environment variables (required for each respective report)

SOL_NODE = os.environ.get("SOL_NODE", "")
ATOM_NODE = os.environ.get("ATOM_NODE", "")
TERRA_LCD_NODE = os.environ.get("TERRA_LCD_NODE", "")

# Optional environment variables
TERRA_FIGMENT_KEY = os.environ.get("TERRA_FIGMENT_KEY", "")

# #############################################################################

TICKER_ATOM = "ATOM"
TICKER_LUNA = "LUNA"
TICKER_SOL = "SOL"
TICKER_OSMO = "OSMO"

DONATION_WALLETS = set([
    os.environ.get("DONATION_WALLET_ATOM", ""),
    os.environ.get("DONATION_WALLET_LUNA", ""),
    os.environ.get("DONATION_WALLET_SOL", ""),
    os.environ.get("DONATION_WALLET_OSMO", ""),
])

MESSAGE_ADDRESS_NOT_FOUND = "Wallet address not found"
MESSAGE_STAKING_ADDRESS_FOUND = "Staking address found.  Please input the main wallet address instead."

REPORTS_DIR = os.path.dirname(os.path.realpath(__file__)) + "/_reports"
