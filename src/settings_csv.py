import os

# Environment variables (required for each respective report)

ALGO_HIST_INDEXER_NODE = os.environ.get("ALGO_HIST_INDEXER_NODE", "https://indexer.algoexplorerapi.io")
ALGO_INDEXER_NODE = os.environ.get("ALGO_INDEXER_NODE", "https://algoindexer.algoexplorerapi.io")
ALGO_NFDOMAINS = os.environ.get("ALGO_NFDOMAINS", "https://api.nf.domains")
ATOM_NODE = os.environ.get("ATOM_NODE", "")
BTSG_NODE = os.environ.get("BTSG_NODE", "https://lcd.explorebitsong.com")
COVALENT_NODE = os.environ.get("COVALENT_NODE", "https://api.covalenthq.com")
DVPN_LCD_NODE = os.environ.get("DVPN_LCD_NODE", "https://lcd.sentinel.co")
DVPN_RPC_NODE = os.environ.get("DVPN_RPC_NODE", "https://rpc.sentinel.co")
EVMOS_NODE = os.environ.get("EVMOS_NODE", "")
FET_NODE = os.environ.get("FET_NODE", "https://rest-fetchhub.fetch.ai")
HUAHUA_NODE = os.environ.get("HUAHUA_NODE", "")
JUNO_NODE = os.environ.get("JUNO_NODE", "")
STARS_NODE = os.environ.get("STARS_NODE", "")
SOL_NODE = os.environ.get("SOL_NODE", "")
TERRA_LCD_NODE = os.environ.get("TERRA_LCD_NODE", "")
LUNA2_LCD_NODE = os.environ.get("LUNA2_LCD_NODE", "https://phoenix-lcd.terra.dev")

# Optional environment variables
COVALENT_API_KEY = os.environ.get("COVALENT_API_KEY", "")

# #############################################################################

TICKER_ALGO = "ALGO"
TICKER_ATOM = "ATOM"
TICKER_BTSG = "BTSG"
TICKER_DVPN = "DVPN"
TICKER_FET = "FET"
TICKER_HUAHUA = "HUAHUA"
TICKER_IOTEX = "IOTX"
TICKER_JUNO = "JUNO"
TICKER_LUNA1 = "LUNA1"
TICKER_LUNA2 = "LUNA2"
TICKER_OSMO = "OSMO"
TICKER_SOL = "SOL"
TICKER_STARS = "STARS"

DONATION_WALLETS = set([v for k, v in os.environ.items() if k.startswith("DONATION_WALLET_")])

MESSAGE_ADDRESS_NOT_FOUND = "Wallet address not found"
MESSAGE_STAKING_ADDRESS_FOUND = "Staking address found.  Please input the main wallet address instead."

REPORTS_DIR = os.path.dirname(os.path.realpath(__file__)) + "/_reports"
