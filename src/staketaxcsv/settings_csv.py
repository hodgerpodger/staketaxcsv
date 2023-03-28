import os

# Environment variables (required for each respective report)

ALGO_HIST_INDEXER_NODE = os.environ.get("STAKETAX_ALGO_HIST_INDEXER_NODE", "https://indexer.algoexplorerapi.io")
ALGO_INDEXER_NODE = os.environ.get("STAKETAX_ALGO_INDEXER_NODE", "https://algoindexer.algoexplorerapi.io")
ALGO_ALT_INDEXER_NODE = os.environ.get("STAKETAX_ALGO_ALT_INDEXER_NODE", "https://mainnet-idx.algonode.cloud")
ALGO_NFDOMAINS = os.environ.get("STAKETAX_ALGO_NFDOMAINS", "https://api.nf.domains")
ATOM_NODE = os.environ.get("STAKETAX_ATOM_NODE", "https://api.cosmos.network")
BLD_NODE = os.environ.get("STAKETAX_BLD_NODE", "https://main.api.agoric.net")
BTSG_NODE = os.environ.get("STAKETAX_BTSG_NODE", "https://lcd.explorebitsong.com")
COVALENT_NODE = os.environ.get("STAKETAX_COVALENT_NODE", "https://api.covalenthq.com")
DVPN_LCD_NODE = os.environ.get("STAKETAX_DVPN_LCD_NODE", "https://lcd.sentinel.co")
DVPN_RPC_NODE = os.environ.get("STAKETAX_DVPN_RPC_NODE", "https://rpc.sentinel.co")
EVMOS_NODE = os.environ.get("STAKETAX_EVMOS_NODE", "")
FET_NODE = os.environ.get("STAKETAX_FET_NODE", "https://rest-fetchhub.fetch.ai")
HUAHUA_NODE = os.environ.get("STAKETAX_HUAHUA_NODE", "")
JUNO_NODE = os.environ.get("STAKETAX_JUNO_NODE", "")
JUNO_RPC_NODES = [
    "https://rpc-archive.junonetwork.io",      # 4136532 to now
    "https://rpc-v3-archive.junonetwork.io",   # 2578099 to #4136530
    "https://rpc-v2-archive.junonetwork.io",   # 1 to #2578097
]
KUJI_NODE = os.environ.get("STAKETAX_KUJI_NODE", "")
KYVE_NODE = os.environ.get("STAKETAX_KYVE_NODE", "https://api-eu-1.kyve.network")
MNTL_NODE = os.environ.get("STAKETAX_MNTL_NODE", "https://rest.assetmantle.one")
OSMO_NODE = os.environ.get("STAKETAX_OSMO_NODE", "https://lcd.osmosis.zone")
REGEN_NODE = os.environ.get("STAKETAX_REGEN_NODE", "")
ROWAN_NODE = os.environ.get("STAKETAX_ROWAN_NODE", "")
SCRT_NODE = os.environ.get("STAKETAX_SCRT_NODE", "")
SOL_NODE = os.environ.get("STAKETAX_SOL_NODE", "https://api.mainnet-beta.solana.com")
STARS_NODE = os.environ.get("STAKETAX_STARS_NODE", "")
STARS_RPC_NODE = os.environ.get("STAKETAX_STARS_RPC_NODE", "")
STARS_RPC_NODES = [STARS_RPC_NODE]
TERRA_LCD_NODE = os.environ.get("STAKETAX_TERRA_LCD_NODE", "")
TORI_NODE = os.environ.get("STAKETAX_TORI_NODE", "")
LUNA2_LCD_NODE = os.environ.get("STAKETAX_LUNA2_LCD_NODE", "https://phoenix-lcd.terra.dev")

# Optional environment variables
COVALENT_API_KEY = os.environ.get("STAKETAX_COVALENT_API_KEY", "")

# #############################################################################

TICKER_ALGO = "ALGO"
TICKER_ATOM = "ATOM"
TICKER_BLD = "BLD"
TICKER_BTSG = "BTSG"
TICKER_DVPN = "DVPN"
TICKER_EVMOS = "EVMOS"
TICKER_FET = "FET"
TICKER_COSMOSPLUS = "COSMOSPLUS"
TICKER_HUAHUA = "HUAHUA"
TICKER_IOTEX = "IOTX"
TICKER_JUNO = "JUNO"
TICKER_KUJI = "KUJI"
TICKER_KYVE = "KYVE"
TICKER_LUNA1 = "LUNA1"
TICKER_LUNA2 = "LUNA2"
TICKER_MNTL = "MNTL"
TICKER_OSMO = "OSMO"
TICKER_REGEN = "REGEN"
TICKER_ROWAN = "ROWAN"
TICKER_SCRT = "SCRT"
TICKER_SOL = "SOL"
TICKER_STARS = "STARS"
TICKER_TORI = "TORI"

DONATION_WALLETS = set([v for k, v in os.environ.items() if k.startswith("DONATION_WALLET_")])

MESSAGE_ADDRESS_NOT_FOUND = "Wallet address not found"
MESSAGE_STAKING_ADDRESS_FOUND = "Staking address found.  Please input the main wallet address instead."

REPORTS_DIR = os.path.dirname(os.path.realpath(__file__)) + "/_reports"
