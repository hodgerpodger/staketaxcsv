import os

# Required for AKT/ARCH/ATOM/DYDX/EVMOS/INJ/JUNO/OSMO/STRD/TIA reports (See https://api.mintscan.io for details on key)
MINTSCAN_KEY = os.environ.get("STAKETAX_MINTSCAN_KEY", "")
MINTSCAN_MAX_TXS = os.environ.get("STAKETAX_MINTSCAN_MAX_TXS", 5000)
MINTSCAN_ON = (MINTSCAN_KEY != "")

# Required for OSMO LP rewards
NUMIA_API_DOMAIN = os.environ.get("STAKETAX_NUMIA_API_DOMAIN", "")
NUMIA_API_TOKEN = os.environ.get("STAKETAX_NUMIA_API_TOKEN", "")

# Environment variables (required for each respective report)

AKT_NODE = os.environ.get("STAKETAX_AKT_NODE", "https://akash-api.polkachu.com")
ALGO_INDEXER_NODE = os.environ.get("STAKETAX_ALGO_INDEXER_NODE", "https://mainnet-idx.algonode.cloud")
ALGO_NFDOMAINS = os.environ.get("STAKETAX_ALGO_NFDOMAINS", "https://api.nf.domains")
ARCH_NODE = os.environ.get("STAKETAX_ARCH_NODE", "https://rest-archway.theamsolutions.info")
ATOM_NODE = os.environ.get("STAKETAX_ATOM_NODE", "https://cosmoshub-api.lavenderfive.com")
BLD_NODE = os.environ.get("STAKETAX_BLD_NODE", "https://main.api.agoric.net")
BLD_NODE_RPC = os.environ.get("STAKETAX_BLD_NODE_RPC", "")
BTSG_NODE = os.environ.get("STAKETAX_BTSG_NODE", "https://lcd.explorebitsong.com")
DVPN_NODE = os.environ.get("STAKETAX_DVPN_NODE", "https://lcd.sentinel.co")
DVPN_NODE_RPC = os.environ.get("STAKETAX_DVPN_NODE_RPC", "https://rpc.sentinel.co")
DYDX_NODE = os.environ.get("STAKETAX_DYDX_NODE", "https://rest-dydx.ecostake.com")
DYM_NODE = os.environ.get("STAKETAX_DYM_NODE", "https://dymension-api.lavenderfive.com")
EVMOS_NODE = os.environ.get("STAKETAX_EVMOS_NODE", "https://rest-evmos.ecostake.com")
FET_NODE = os.environ.get("STAKETAX_FET_NODE", "https://rest-fetchhub.fetch.ai")
GRAV_NODE = os.environ.get("STAKETAX_GRAV_NODE", "https://gravitychain.io:26657")
GRAV_NODE_RPC = os.environ.get("STAKETAX_GRAV_NODE_RPC", "")
HUAHUA_NODE = os.environ.get("STAKETAX_HUAHUA_NODE", "")
INJ_NODE = os.environ.get("STAKETAX_INJ_NODE", "https://injective-api.polkachu.com")
JUNO_NODE = os.environ.get("STAKETAX_JUNO_NODE", "https://juno-api.polkachu.com")
KUJI_NODE = os.environ.get("STAKETAX_KUJI_NODE", "")
KUJI_NODE_TXS = os.environ.get("STAKETAX_KUJI_NODE_TXS", KUJI_NODE)
KYVE_NODE = os.environ.get("STAKETAX_KYVE_NODE", "https://api-eu-1.kyve.network")
LUNA1_NODE = os.environ.get("STAKETAX_LUNA1_NODE", "https://terra-classic-lcd.publicnode.com")
LUNA2_NODE = os.environ.get("STAKETAX_LUNA2_NODE", "https://terra-lcd.publicnode.com")
MNTL_NODE = os.environ.get("STAKETAX_MNTL_NODE", "https://rest.assetmantle.one")
NLS_NODE = os.environ.get("STAKETAX_NLS_NODE", "https://pirin-cl-arc.nolus.network:1317")
NTRN_NODE = os.environ.get("STAKETAX_NTRN_NODE", "https://rest.cosmos.directory/neutron")
OSMO_NODE = os.environ.get("STAKETAX_OSMO_NODE", "https://lcd.osmosis.zone")
REGEN_NODE = os.environ.get("STAKETAX_REGEN_NODE", "")
ROWAN_NODE = os.environ.get("STAKETAX_ROWAN_NODE", "")
SAGA_NODE = os.environ.get("STAKETAX_SAGA_NODE", "https://saga-api.polkachu.com")
SCRT_NODE = os.environ.get("STAKETAX_SCRT_NODE", "")
SEI_NODE = os.environ.get("STAKETAX_SEI_NODE", "https://sei-api.polkachu.com/")
SOL_NODE = os.environ.get("STAKETAX_SOL_NODE", "https://api.mainnet-beta.solana.com")
STARS_NODE = os.environ.get("STAKETAX_STARS_NODE", "")
STARS_NODE_RPC = os.environ.get("STAKETAX_STARS_NODE_RPC", "")
STRD_NODE = os.environ.get("STAKETAX_STRD_NODE", "https://lcd-stride.whispernode.com")
TIA_NODE = os.environ.get("STAKETAX_TIA_NODE", "https://celestia.api.kjnodes.com")
TORI_NODE = os.environ.get("STAKETAX_TORI_NODE", "")

# ########## Optional environment variables ########################################################
DB_CACHE = os.environ.get("STAKETAX_DB_CACHE", False)

# ### One of below required for faster solana staking rewards history
# (flipside free tier is sufficient; solscan api costs money; db method has issues after 12/2024)

SOL_REWARDS_SOLSCAN_API_TOKEN = os.environ.get("STAKETAX_SOL_REWARDS_SOLSCAN_API_TOKEN", "")
SOL_REWARDS_FLIPSIDE_API_KEY = os.environ.get("STAKETAX_SOL_REWARDS_FLIPSIDE_API_KEY", "")
SOL_REWARDS_USE_DB = os.environ.get("STAKETAX_SOL_REWARDS_USE_DB", False)

# ###

# #############################################################################

TICKER_AKT = "AKT"
TICKER_ALGO = "ALGO"
TICKER_ARCH = "ARCH"
TICKER_ATOM = "ATOM"
TICKER_BLD = "BLD"
TICKER_BTSG = "BTSG"
TICKER_DVPN = "DVPN"
TICKER_DYDX = "DYDX"
TICKER_DYM = "DYM"
TICKER_EVMOS = "EVMOS"
TICKER_FET = "FET"
TICKER_GRAV = "GRAV"
TICKER_COSMOSPLUS = "COSMOSPLUS"
TICKER_HUAHUA = "HUAHUA"
TICKER_IOTEX = "IOTX"
TICKER_JUNO = "JUNO"
TICKER_KUJI = "KUJI"
TICKER_KYVE = "KYVE"
TICKER_INJ = "INJ"
TICKER_LUNA1 = "LUNA1"
TICKER_LUNA2 = "LUNA2"
TICKER_MNTL = "MNTL"
TICKER_NLS = "NLS"
TICKER_NTRN = "NTRN"
TICKER_OSMO = "OSMO"
TICKER_REGEN = "REGEN"
TICKER_ROWAN = "ROWAN"
TICKER_SAGA = "SAGA"
TICKER_SCRT = "SCRT"
TICKER_SEI = "SEI"
TICKER_SOL = "SOL"
TICKER_STARS = "STARS"
TICKER_STRD = "STRD"
TICKER_TIA = "TIA"
TICKER_TORI = "TORI"

DONATION_WALLETS = set([v for k, v in os.environ.items() if k.startswith("DONATION_WALLET_")])

MESSAGE_ADDRESS_NOT_FOUND = "Wallet address not found"
MESSAGE_STAKING_ADDRESS_FOUND = "Staking address found.  Please input the main wallet address instead."

REPORTS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "_reports")
