import base64

from algosdk import encoding
from functools import partial
from staketaxcsv.algo import constants as co
from staketaxcsv.algo.asset import Algo, Asset
from staketaxcsv.algo.export_tx import (
    export_airdrop_tx,
    export_borrow_tx,
    export_deposit_collateral_tx,
    export_income_tx,
    export_lp_deposit_tx,
    export_lp_withdraw_tx,
    export_repay_tx,
    export_reward_tx,
    export_stake_tx,
    export_swap_tx,
    export_unknown,
    export_unstake_tx,
    export_withdraw_collateral_tx,
)
from staketaxcsv.algo.transaction import (
    generate_inner_transfer_assets,
    get_fee_amount,
    get_inner_transfer_asset,
    get_transfer_asset,
    is_algo_transfer,
    is_app_call,
    is_asset_optin,
    is_transfer,
    is_transfer_receiver,
    is_transfer_receiver_non_zero_asset
)

# For reference
# https://github.com/Algofiorg/algofi-python-sdk
# https://github.com/Algofiorg/algofi-javascript-sdk

COMMENT_ALGOFIV2 = "AlgoFi"

APPLICATION_ID_ALGOFIV2_LENDING_MANAGER = 818176933
APPLICATION_ID_ALGOFIV2_LENDING_POOL_MANAGER = 841165954
APPLICATION_ID_ALGOFIV2_VALGO_MARKET = 879935316
APPLICATION_ID_ALGOFIV2_GOVERNANCE_ADMIN = 900653388
APPLICATION_ID_ALGOFIV2_GOVERNANCE_VOTING_ESCROW = 900653165
APPLICATION_ID_ALGOFIV2_GOVERNANCE_REWARDS_MANAGER = 900652834

ALGOFIV2_TRANSACTION_USER_OPTIN = "dW9p"                    # "uoi"
ALGOFIV2_TRANSACTION_MARKET_OPTIN = "dW1vaQ=="              # "umoi"
ALGOFIV2_TRANSACTION_MARKET_CLOSEOUT = "dW1jbw=="           # "umco"
ALGOFIV2_TRANSACTION_VALIDATE_MARKET = "dm0="               # "vm"
ALGOFIV2_TRANSACTION_ADD_UNDERLYING_COLLATERAL = "YXVj"     # "auc"
ALGOFIV2_TRANSACTION_REMOVE_UNDERLYING_COLLATERAL = "cnVj"  # "ruc"
ALGOFIV2_TRANSACTION_BORROW = "Yg=="                        # "b"
ALGOFIV2_TRANSACTION_REPAY_BORROW = "cmI="                  # "rb"

ALGOFIV2_TRANSACTION_MINT_B_ASSET = "bWJh"                  # "mba"
ALGOFIV2_TRANSACTION_BURN_B_ASSET = "YnI="                  # "br"
ALGOFIV2_TRANSACTION_FARM_OPS = "Zm8="                      # "fo"
ALGOFIV2_TRANSACTION_STAKE = "cw=="                         # "s"
ALGOFIV2_TRANSACTION_UNSTAKE = "dQ=="                       # "u"

ALGOFIV2_TRANSACTION_CLAIM_REWARDS = "Y3I="                 # "cr"

ALGOFIV2_TRANSACTION_STORAGE_OPTIN = "c2FvaQ=="             # "saoi"
ALGOFIV2_TRANSACTION_USER_OPTIN = "dW9p"                    # "uoi"
ALGOFIV2_TRANSACTION_LOCK = "bA=="                          # "l"
ALGOFIV2_TRANSACTION_INCREASE_LOCK_AMOUNT = "aWxh"          # "ila"

ALGOFIV2_TRANSACTION_SWAP_STEP_1 = "c3dhcF9zdGVwXzE="       # "swap_step_1"
ALGOFIV2_TRANSACTION_SWAP_STEP_2 = "c3dhcF9zdGVwXzI="       # "swap_step_2"
ALGOFIV2_TRANSACTION_SWAP_STEP_3 = "c3dhcF9zdGVwXzM="       # "swap_step_3"
ALGOFIV2_TRANSACTION_SWAP_STEP_4 = "c3dhcF9zdGVwXzQ="       # "swap_step_4"
ALGOFIV2_TRANSACTION_SWAP_STEP_5 = "c3dhcF9zdGVwXzU="       # "swap_step_5"
ALGOFIV2_TRANSACTION_POOL_STEP_1 = "cG9vbF9zdGVwXzE="       # "pool_step_1"
ALGOFIV2_TRANSACTION_POOL_STEP_2 = "cG9vbF9zdGVwXzI="       # "pool_step_2"
ALGOFIV2_TRANSACTION_POOL_STEP_3 = "cG9vbF9zdGVwXzM="       # "pool_step_3"
ALGOFIV2_TRANSACTION_POOL_STEP_5 = "cG9vbF9zdGVwXzU="       # "pool_step_5"
ALGOFIV2_TRANSACTION_POOL_STEP_6 = "cG9vbF9zdGVwXzY="       # "pool_step_6"
ALGOFIV2_TRANSACTION_POOL_STEP_7 = "cG9vbF9zdGVwXzc="       # "pool_step_7"
ALGOFIV2_TRANSACTION_BURN_STEP_1 = "YnVybl9zdGVwXzE="       # "burn_step_1"
ALGOFIV2_TRANSACTION_BURN_STEP_2 = "YnVybl9zdGVwXzI="       # "burn_step_2"
ALGOFIV2_TRANSACTION_BURN_STEP_3 = "YnVybl9zdGVwXzM="       # "burn_step_3"
ALGOFIV2_TRANSACTION_BURN_STEP_4 = "YnVybl9zdGVwXzQ="       # "burn_step_4"

ALGOFIV2_STATE_KEY_USER_AMOUNT_LOCKED = "YWFs"  # "aal"

ALGOFIV2_MANAGER_STORAGE_ACCOUNT = "c2E="  # "sa"

ASSET_ID_BANK = 900652777

UNDERLYING_ASSETS = {
    # bALGO -> ALGO
    818179690: 0,
    # bUSDC -> USDC
    818182311: 31566704,
    # bgoBTC -> goBTC
    818184214: 386192725,
    # bgoETH -> goETH
    818188553: 386195940,
    # bUSDT -> USDT
    818190568: 312769,
    # bSTBL2 -> STBL2
    841157954: 841126810,
    # bvALGO -> vALGO
    879951266: 0,
    # bSTBL2-USDC-LP -> STBL2-USDC-LP
    841462373: 841171328,
    # bSTBL2-ALGO-LP -> STBL2-ALGO-LP
    856217307: 855717054,
    # bSTBL2-goBTC-LP -> STBL2-goBTC-LP
    870380101: 870151164,
    # bSTBL2-goETH-LP -> STBL2-goETH-LP
    870391958: 870150187,
    # bBANK -> BANK
    900919286: 900652777,
}

ALGOFIV2_MARKET_CONTRACTS = [
    818179346,  # ALGO
    818182048,  # USDC
    818183964,  # goBTC
    818188286,  # goETH
    818190205,  # USDT
    841145020,  # STBL2
    841194726,  # STBL2-USDC-LP
    856183130,  # STBL2-ALGO-LP
    870271921,  # STBL2-goBTC-LP
    870275741,  # STBL2-goETH-LP
    879935316,  # vALGO
    900883415,  # BANK
]

ALGOFIV2_STAKING_CONTRACTS = [
    821882730,  # USDC
    821882927,  # USDT
    900932886,  # STBL2/BANK LP
    919964086,  # ALGO/USDC LP
    919964388,  # STBL2/ALGO LP
    919965019,  # STBL2/goBTC LP
    919965630,  # STBL2/goETH LP
    962407544,  # ALGO/BANK LP
]

ALGOFIV2_LENDING_CONTRACTS = [
    841198034,  # USDC / STBL2
    856198764,  # ALGO / STBL2
    870281048,  # goBTC / STBL2
    870281567,  # goETH / STBL2
    900930380,  # STBL2 / BANK
    919954173,  # ALGO / USDC
    962381193,  # ALGO / BANK
]


def get_algofiv2_storage_address(account):
    app_local_state = account.get("apps-local-state", [])
    for app in app_local_state:
        if app["id"] == APPLICATION_ID_ALGOFIV2_LENDING_MANAGER:
            for keyvalue in app.get("key-value", []):
                if keyvalue["key"] == ALGOFIV2_MANAGER_STORAGE_ACCOUNT:
                    raw_address = keyvalue["value"]["bytes"]
                    return encoding.encode_address(base64.b64decode(raw_address.strip()))

    return None


def _is_algofiv2_user_optin(group):
    if len(group) != 2:
        return False

    if not is_transfer(group[0]):
        return False

    return is_app_call(group[1], APPLICATION_ID_ALGOFIV2_LENDING_MANAGER, ALGOFIV2_TRANSACTION_USER_OPTIN)


def _is_algofiv2_market_optin(group):
    if len(group) != 3:
        return False

    if not is_transfer(group[0]):
        return False

    if not is_app_call(group[1], APPLICATION_ID_ALGOFIV2_LENDING_MANAGER, ALGOFIV2_TRANSACTION_VALIDATE_MARKET):
        return False

    return is_app_call(group[2], APPLICATION_ID_ALGOFIV2_LENDING_MANAGER, ALGOFIV2_TRANSACTION_MARKET_OPTIN)


def _is_algofiv2_deposit_collateral(group):
    length = len(group)
    if length != 2 and length != 3:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    if not is_transfer(group[i]):
        return False

    return is_app_call(group[-1],
                       ALGOFIV2_MARKET_CONTRACTS,
                       ALGOFIV2_TRANSACTION_ADD_UNDERLYING_COLLATERAL,
                       APPLICATION_ID_ALGOFIV2_LENDING_MANAGER)


def _is_algofiv2_withdraw_collateral(group):
    if len(group) != 1:
        return False

    return is_app_call(group[0], ALGOFIV2_MARKET_CONTRACTS, ALGOFIV2_TRANSACTION_REMOVE_UNDERLYING_COLLATERAL)


def _is_algofiv2_borrow(group):
    return is_app_call(group[-1],
                       ALGOFIV2_MARKET_CONTRACTS,
                       ALGOFIV2_TRANSACTION_BORROW,
                       APPLICATION_ID_ALGOFIV2_LENDING_MANAGER)


def _is_algofiv2_repay_borrow(group):
    length = len(group)
    if length < 2 or length > 4:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1
    if is_asset_optin(group[i]):
        i += 1

    if i == length:
        return False

    if not is_transfer(group[i]):
        return False

    return is_app_call(group[-1],
                       ALGOFIV2_MARKET_CONTRACTS,
                       ALGOFIV2_TRANSACTION_REPAY_BORROW,
                       APPLICATION_ID_ALGOFIV2_LENDING_MANAGER)


def _is_algofiv2_farm_stake(group):
    if len(group) != 3:
        return False

    if not is_app_call(group[0], ALGOFIV2_STAKING_CONTRACTS, ALGOFIV2_TRANSACTION_FARM_OPS):
        return False

    if not is_transfer(group[1]):
        return False

    return is_app_call(group[2], ALGOFIV2_STAKING_CONTRACTS, ALGOFIV2_TRANSACTION_STAKE)


def _is_algofiv2_farm_unstake(group):
    if len(group) != 2:
        return False

    if not is_app_call(group[0], ALGOFIV2_STAKING_CONTRACTS, ALGOFIV2_TRANSACTION_FARM_OPS):
        return False

    return is_app_call(group[1], ALGOFIV2_STAKING_CONTRACTS, ALGOFIV2_TRANSACTION_UNSTAKE)


def _is_algofiv2_lend_stake(group):
    length = len(group)
    if length != 5 and length != 6:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    if not is_transfer(group[i]):
        return False

    if not is_app_call(group[i + 1], ALGOFIV2_MARKET_CONTRACTS, ALGOFIV2_TRANSACTION_MINT_B_ASSET):
        return False

    if not is_app_call(group[i + 2], ALGOFIV2_STAKING_CONTRACTS, ALGOFIV2_TRANSACTION_FARM_OPS):
        return False

    return is_app_call(group[i + 4], ALGOFIV2_STAKING_CONTRACTS, ALGOFIV2_TRANSACTION_STAKE)


def _is_algofiv2_lend_unstake(group):
    if len(group) != 4:
        return False

    if not is_app_call(group[0], ALGOFIV2_STAKING_CONTRACTS, ALGOFIV2_TRANSACTION_FARM_OPS):
        return False

    if not is_app_call(group[1], ALGOFIV2_STAKING_CONTRACTS, ALGOFIV2_TRANSACTION_UNSTAKE):
        return False

    if not is_transfer(group[2]):
        return False

    return is_app_call(group[3], ALGOFIV2_MARKET_CONTRACTS, ALGOFIV2_TRANSACTION_BURN_B_ASSET)


def _is_algofiv2_governance_optin(group):
    if len(group) != 5:
        return False

    if not is_algo_transfer(group[0]):
        return False

    if not is_app_call(group[1], APPLICATION_ID_ALGOFIV2_GOVERNANCE_ADMIN, ALGOFIV2_TRANSACTION_STORAGE_OPTIN):
        return False

    if not is_app_call(group[2], APPLICATION_ID_ALGOFIV2_GOVERNANCE_ADMIN, ALGOFIV2_TRANSACTION_USER_OPTIN):
        return False

    if (not is_app_call(group[3],
                        APPLICATION_ID_ALGOFIV2_GOVERNANCE_VOTING_ESCROW,
                        foreign_app=APPLICATION_ID_ALGOFIV2_GOVERNANCE_REWARDS_MANAGER)):
        return False

    return is_app_call(group[4], APPLICATION_ID_ALGOFIV2_GOVERNANCE_REWARDS_MANAGER, ALGOFIV2_TRANSACTION_USER_OPTIN)


def _is_algofiv2_governance_airdrop(group):
    length = len(group)
    if length != 7 and length != 8:
        return False

    if not _is_algofiv2_governance_optin(group[:5]):
        return False

    return is_app_call(group[-1], APPLICATION_ID_ALGOFIV2_GOVERNANCE_VOTING_ESCROW, ALGOFIV2_TRANSACTION_LOCK)


def _is_algofiv2_governance_increase_lock(group):
    if len(group) < 2:
        return False

    if not is_transfer(group[0]):
        return False

    return is_app_call(group[1],
                       APPLICATION_ID_ALGOFIV2_GOVERNANCE_VOTING_ESCROW,
                       [ALGOFIV2_TRANSACTION_INCREASE_LOCK_AMOUNT, ALGOFIV2_TRANSACTION_LOCK])


def _is_algofiv2_claim_staking_rewards(group):
    length = len(group)
    if length < 2:
        return False

    i = 0
    while i < length:
        if is_asset_optin(group[i]):
            i += 1

        if not is_app_call(group[i], ALGOFIV2_STAKING_CONTRACTS, ALGOFIV2_TRANSACTION_FARM_OPS):
            return False

        if (not is_app_call(group[i + 1],
                            ALGOFIV2_STAKING_CONTRACTS,
                            ALGOFIV2_TRANSACTION_CLAIM_REWARDS,
                            APPLICATION_ID_ALGOFIV2_GOVERNANCE_VOTING_ESCROW)):
            return False
        i += 2

    return True


def _is_algofiv2_claim_lending_rewards(group):
    length = len(group)

    i = 0
    while i < length:
        if is_asset_optin(group[i]):
            i += 1

        if i == length:
            return False

        if (not is_app_call(group[i],
                            ALGOFIV2_MARKET_CONTRACTS,
                            ALGOFIV2_TRANSACTION_CLAIM_REWARDS,
                            APPLICATION_ID_ALGOFIV2_LENDING_MANAGER)):
            return False

        i += 2

    return True


def _is_algofiv2_lend_swap(group):
    length = len(group)
    if length < 5 or length > 7:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1
    if is_asset_optin(group[i]):
        i += 1

    if not is_transfer(group[i]):
        return False

    if not is_app_call(group[i + 1], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_SWAP_STEP_1):
        return False

    if not is_app_call(group[i + 2], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_SWAP_STEP_2):
        return False

    # Step 3 does not reference the user account, so it won't appear in the tx list

    if not is_app_call(group[i + 3], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_SWAP_STEP_4):
        return False

    return is_app_call(group[i + 4], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_SWAP_STEP_5)


def _is_algofiv2_pool_swap(group):
    length = len(group)
    if length < 4 or length > 6:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1
    if is_asset_optin(group[i]):
        i += 1

    if not is_transfer(group[i]):
        return False

    if not is_app_call(group[i + 1],
                       app_args=ALGOFIV2_TRANSACTION_SWAP_STEP_1,
                       foreign_app=APPLICATION_ID_ALGOFIV2_LENDING_MANAGER):
        return False

    if not is_app_call(group[i + 2],
                       app_args=ALGOFIV2_TRANSACTION_SWAP_STEP_2,
                       foreign_app=APPLICATION_ID_ALGOFIV2_LENDING_POOL_MANAGER):
        return False

    return is_app_call(group[i + 3],
                       app_args=ALGOFIV2_TRANSACTION_SWAP_STEP_3,
                       foreign_app=APPLICATION_ID_ALGOFIV2_LENDING_MANAGER)


def _is_algofiv2_lend_lp_add(group):
    length = len(group)
    if length < 6 or length > 7:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    if not is_transfer(group[i]):
        return False

    if not is_transfer(group[i + 1]):
        return False

    if not is_app_call(group[i + 2], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_POOL_STEP_1):
        return False

    # Steps 2-4 do not reference the user account, so they won't appear in the tx list

    if not is_app_call(group[i + 3], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_POOL_STEP_5):
        return False

    if not is_app_call(group[i + 4], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_POOL_STEP_6):
        return False

    return is_app_call(group[i + 5], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_POOL_STEP_7)


def _is_algofiv2_pool_lp_add(group):
    length = len(group)
    if length < 5 or length > 6:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    if not is_transfer(group[i]):
        return False

    if not is_transfer(group[i + 1]):
        return False

    if not is_app_call(group[i + 2],
                       app_args=ALGOFIV2_TRANSACTION_POOL_STEP_1,
                       foreign_app=APPLICATION_ID_ALGOFIV2_LENDING_MANAGER):
        return False

    if not is_app_call(group[i + 3],
                       app_args=ALGOFIV2_TRANSACTION_POOL_STEP_2,
                       foreign_app=APPLICATION_ID_ALGOFIV2_LENDING_POOL_MANAGER):
        return False

    return is_app_call(group[i + 4],
                       app_args=ALGOFIV2_TRANSACTION_POOL_STEP_3,
                       foreign_app=APPLICATION_ID_ALGOFIV2_LENDING_MANAGER)


def _is_algofiv2_lend_lp_remove(group):
    length = len(group)
    if length < 4 or length > 6:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1
    if is_asset_optin(group[i]):
        i += 1

    if not is_transfer(group[i]):
        return False

    asset = get_transfer_asset(group[i])
    if not asset.is_lp_token():
        return False

    if not is_app_call(group[i + 1], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_BURN_STEP_1):
        return False

    # Step 2 does not reference the user account, so it won't appear in the tx list

    if not is_app_call(group[i + 2], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_BURN_STEP_3):
        return False

    return is_app_call(group[i + 3], ALGOFIV2_LENDING_CONTRACTS, ALGOFIV2_TRANSACTION_BURN_STEP_4)


def _is_algofiv2_pool_lp_remove(group):
    length = len(group)
    if length < 3 or length > 5:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1
    if is_asset_optin(group[i]):
        i += 1

    if not is_transfer(group[i]):
        return False

    asset = get_transfer_asset(group[i])
    if not asset.is_lp_token():
        return False

    if not is_app_call(group[i + 1],
                       app_args=ALGOFIV2_TRANSACTION_BURN_STEP_1,
                       foreign_app=APPLICATION_ID_ALGOFIV2_LENDING_POOL_MANAGER):
        return False

    return is_app_call(group[i + 2],
                       app_args=ALGOFIV2_TRANSACTION_BURN_STEP_2,
                       foreign_app=APPLICATION_ID_ALGOFIV2_LENDING_POOL_MANAGER)


def _is_algofiv2_lend_zap(group):
    length = len(group)
    if length < 11 or length > 14:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1
    if is_asset_optin(group[i]):
        i += 1

    return _is_algofiv2_lend_swap(group[:i + 5]) and _is_algofiv2_lend_lp_add(group[i + 5:])


def _is_algofiv2_pool_zap(group):
    length = len(group)
    if length < 9 or length > 12:
        return False

    i = 0
    if is_asset_optin(group[i]):
        i += 1
    if is_asset_optin(group[i]):
        i += 1

    return _is_algofiv2_pool_swap(group[:i + 4]) and _is_algofiv2_pool_lp_add(group[i + 4:])


def _is_algofiv2_market_closeout(group):
    if len(group) != 1:
        return False

    return is_app_call(group[0], APPLICATION_ID_ALGOFIV2_LENDING_MANAGER, ALGOFIV2_TRANSACTION_MARKET_CLOSEOUT)


def is_algofiv2_transaction(group):
    return (_is_algofiv2_lend_swap(group)
                or _is_algofiv2_pool_swap(group)
                or _is_algofiv2_claim_staking_rewards(group)
                or _is_algofiv2_claim_lending_rewards(group)
                or _is_algofiv2_deposit_collateral(group)
                or _is_algofiv2_withdraw_collateral(group)
                or _is_algofiv2_borrow(group)
                or _is_algofiv2_repay_borrow(group)
                or _is_algofiv2_farm_stake(group)
                or _is_algofiv2_farm_unstake(group)
                or _is_algofiv2_lend_stake(group)
                or _is_algofiv2_lend_unstake(group)
                or _is_algofiv2_lend_lp_add(group)
                or _is_algofiv2_pool_lp_add(group)
                or _is_algofiv2_lend_lp_remove(group)
                or _is_algofiv2_pool_lp_remove(group)
                or _is_algofiv2_lend_zap(group)
                or _is_algofiv2_pool_zap(group)
                or _is_algofiv2_user_optin(group)
                or _is_algofiv2_market_optin(group)
                or _is_algofiv2_market_closeout(group)
                or _is_algofiv2_governance_airdrop(group)
                or _is_algofiv2_governance_optin(group)
                or _is_algofiv2_governance_increase_lock(group))


def handle_algofiv2_transaction(wallet_address, group, exporter, txinfo):
    if _is_algofiv2_lend_swap(group):
        _handle_algofiv2_lend_swap(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_pool_swap(group):
        _handle_algofiv2_pool_swap(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_claim_staking_rewards(group):
        _handle_algofiv2_claim_staking_rewards(group, exporter, txinfo)

    elif _is_algofiv2_claim_lending_rewards(group):
        _handle_algofiv2_claim_lending_rewards(group, exporter, txinfo)

    elif _is_algofiv2_deposit_collateral(group):
        _handle_algofiv2_deposit_collateral(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_withdraw_collateral(group):
        _handle_algofiv2_withdraw_collateral(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_borrow(group):
        _handle_algofiv2_borrow(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_repay_borrow(group):
        _handle_algofiv2_repay_borrow(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_farm_stake(group):
        _handle_algofiv2_farm_stake(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_farm_unstake(group):
        _handle_algofiv2_farm_unstake(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_lend_stake(group):
        _handle_algofiv2_lend_stake(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_lend_unstake(group):
        _handle_algofiv2_lend_unstake(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_lend_lp_add(group):
        _handle_algofiv2_lend_lp_add(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_pool_lp_add(group):
        _handle_algofiv2_pool_lp_add(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_lend_lp_remove(group):
        _handle_algofiv2_lend_lp_remove(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_pool_lp_remove(group):
        _handle_algofiv2_pool_lp_remove(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_lend_zap(group):
        _handle_algofiv2_lend_zap(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_pool_zap(group):
        _handle_algofiv2_pool_zap(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_user_optin(group):
        pass

    elif _is_algofiv2_market_optin(group):
        pass

    elif _is_algofiv2_market_closeout(group):
        pass

    elif _is_algofiv2_governance_increase_lock(group):
        _handle_algofiv2_governance_increase_lock(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_governance_airdrop(group):
        _handle_algofiv2_governance_airdrop(wallet_address, group, exporter, txinfo)

    elif _is_algofiv2_governance_optin(group):
        pass

    else:
        export_unknown(exporter, txinfo)


def _handle_algofiv2_deposit_collateral(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_transaction = group[0]
    if is_asset_optin(send_transaction):
        send_transaction = group[1]

    send_asset = get_transfer_asset(send_transaction)

    app_transaction = group[-1]
    app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    comment = COMMENT_ALGOFIV2 + (" Vault" if app_id == APPLICATION_ID_ALGOFIV2_VALGO_MARKET else "")

    export_deposit_collateral_tx(exporter, txinfo, send_asset, fee_amount, comment)


def _handle_algofiv2_withdraw_collateral(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    app_transaction = group[-1]
    receive_asset = get_inner_transfer_asset(app_transaction)
    app_id = app_transaction[co.TRANSACTION_KEY_APP_CALL]["application-id"]
    comment = COMMENT_ALGOFIV2 + (" Vault" if app_id == APPLICATION_ID_ALGOFIV2_VALGO_MARKET else "")

    export_withdraw_collateral_tx(exporter, txinfo, receive_asset, fee_amount, comment)


def _handle_algofiv2_borrow(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    app_transaction = group[-1]
    receive_asset = get_inner_transfer_asset(app_transaction)

    export_borrow_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_ALGOFIV2 + " Borrow")


def _handle_algofiv2_repay_borrow(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_asset = get_transfer_asset(group[-2])
    redeem_asset = get_inner_transfer_asset(group[-1])
    if redeem_asset is not None:
        send_asset -= redeem_asset

    export_repay_tx(exporter, txinfo, send_asset, fee_amount, COMMENT_ALGOFIV2 + " Repay")


def _handle_algofiv2_farm_stake(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_transaction = group[1]
    send_asset = get_transfer_asset(send_transaction)

    export_stake_tx(exporter, txinfo, send_asset, fee_amount, COMMENT_ALGOFIV2)


def _handle_algofiv2_farm_unstake(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    app_transaction = group[1]
    receive_asset = get_inner_transfer_asset(app_transaction)
    export_unstake_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_ALGOFIV2)


def _handle_algofiv2_lend_stake(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_transaction = group[0]
    if is_asset_optin(send_transaction):
        send_transaction = group[1]

    send_asset = get_transfer_asset(send_transaction)

    export_stake_tx(exporter, txinfo, send_asset, fee_amount, COMMENT_ALGOFIV2)


def _handle_algofiv2_lend_unstake(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_transaction = group[2]
    send_asset = get_transfer_asset(send_transaction, UNDERLYING_ASSETS)

    app_transaction = group[3]
    receive_asset = get_inner_transfer_asset(app_transaction)
    export_unstake_tx(exporter, txinfo, receive_asset, 0, COMMENT_ALGOFIV2, 0)
    # TODO will need to track cost basis to calculate earnings accurately
    # https://github.com/hodgerpodger/staketaxcsv/issues/245
    # export_income_tx(exporter, txinfo, receive_asset - send_asset, fee_amount, COMMENT_ALGOFIV2, 1)


def _handle_algofiv2_governance_airdrop(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    receive_transaction = group[5]
    if is_asset_optin(receive_transaction):
        receive_transaction = group[6]

    receive_asset = get_transfer_asset(receive_transaction)
    export_airdrop_tx(exporter, txinfo, receive_asset, fee_amount, COMMENT_ALGOFIV2, 0)

    lock_transaction = group[-1]
    local_state_deltas = lock_transaction["local-state-delta"][0]["delta"]
    for pair in local_state_deltas:
        if pair["key"] == ALGOFIV2_STATE_KEY_USER_AMOUNT_LOCKED:
            send_asset = Asset(ASSET_ID_BANK, pair["value"]["uint"])
            export_stake_tx(exporter, txinfo, send_asset, 0, COMMENT_ALGOFIV2, 1)
            break


def _handle_algofiv2_governance_increase_lock(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    send_transaction = group[0]
    send_asset = get_transfer_asset(send_transaction)
    export_stake_tx(exporter, txinfo, send_asset, fee_amount, COMMENT_ALGOFIV2)


def _handle_algofiv2_claim_staking_rewards(group, exporter, txinfo):
    length = len(group)

    i = 0
    z_index = 0
    while i < length:
        fee_amount = 0
        transaction = group[i]
        if is_asset_optin(transaction):
            fee_amount += transaction["fee"]
            i += 1

        transaction = group[i]
        fee_amount += transaction["fee"]

        transaction = group[i + 1]
        fee_amount += transaction["fee"]
        reward_asset = get_inner_transfer_asset(transaction)
        export_reward_tx(exporter, txinfo, reward_asset, fee_amount, COMMENT_ALGOFIV2, z_index)
        i += 2
        z_index += 1


def _handle_algofiv2_claim_lending_rewards(group, exporter, txinfo):
    length = len(group)

    rewards = {}
    fees = {}
    i = 0
    while i < length:
        fee_amount = 0
        transaction = group[i]
        if is_asset_optin(transaction):
            fee_amount += transaction["fee"]
            i += 1

        transaction = group[i]
        fee_amount += transaction["fee"]
        reward_asset = get_inner_transfer_asset(transaction)
        rewards[reward_asset.id] = reward_asset + rewards.get(reward_asset.id, 0)
        fees[reward_asset.id] = fee_amount + fees.get(reward_asset.id, 0)
        i += 1

    z_index = 0
    for key, value in rewards.items():
        export_reward_tx(exporter, txinfo, value, fees[key], COMMENT_ALGOFIV2, z_index)
        z_index += 1


def _handle_algofiv2_lend_swap(wallet_address, group, exporter, txinfo, z_index=0):
    fee_amount = get_fee_amount(wallet_address, group)

    i = 0
    while is_asset_optin(group[i]):
        i += 1
    send_asset = get_transfer_asset(group[i])

    receive_asset_1 = get_inner_transfer_asset(group[i + 3],
                                               filter=partial(is_transfer_receiver, wallet_address))

    receive_asset_2 = get_inner_transfer_asset(group[i + 4],
                                               filter=partial(is_transfer_receiver, wallet_address))
    if receive_asset_1.id == send_asset.id:
        send_asset -= receive_asset_1
        receive_asset = receive_asset_2
    else:
        send_asset -= receive_asset_2
        receive_asset = receive_asset_1

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_ALGOFIV2, z_index)


def _handle_algofiv2_pool_swap(wallet_address, group, exporter, txinfo, z_index=0):
    fee_amount = get_fee_amount(wallet_address, group)

    i = 0
    while is_asset_optin(group[i]):
        i += 1

    send_asset = get_transfer_asset(group[i])

    receive_assets = list(generate_inner_transfer_assets(
        group[i + 3], filter=partial(is_transfer_receiver_non_zero_asset, wallet_address)))

    if len(receive_assets) > 2:
        export_unknown(exporter, txinfo)
        return

    receive_asset = None
    for asset in receive_assets:
        if asset.id == send_asset.id:
            send_asset -= asset
        else:
            receive_asset = asset

    export_swap_tx(exporter, txinfo, send_asset, receive_asset, fee_amount, COMMENT_ALGOFIV2, z_index)


def _handle_algofiv2_lend_lp_add(wallet_address, group, exporter, txinfo, z_index=0):
    fee_amount = get_fee_amount(wallet_address, group)

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    send_asset_1 = get_transfer_asset(group[i])
    send_asset_2 = get_transfer_asset(group[i + 1])

    lp_asset = get_inner_transfer_asset(group[i + 3])

    redeem_asset_1 = get_inner_transfer_asset(group[i + 4],
                                              filter=partial(is_transfer_receiver, wallet_address))
    if redeem_asset_1 is not None:
        send_asset_1 -= redeem_asset_1

    redeem_asset_2 = get_inner_transfer_asset(group[i + 5],
                                              filter=partial(is_transfer_receiver, wallet_address))
    if redeem_asset_2 is not None:
        send_asset_2 -= redeem_asset_2

    export_lp_deposit_tx(
        exporter, txinfo,
        send_asset_1, send_asset_2, lp_asset,
        fee_amount, COMMENT_ALGOFIV2, z_index)


def _handle_algofiv2_pool_lp_add(wallet_address, group, exporter, txinfo, z_index=0):
    fee_amount = get_fee_amount(wallet_address, group)

    i = 0
    if is_asset_optin(group[i]):
        i += 1

    send_asset_1 = get_transfer_asset(group[i])
    send_asset_2 = get_transfer_asset(group[i + 1])

    lp_asset = get_inner_transfer_asset(group[i + 3], filter=partial(is_transfer_receiver, wallet_address))

    redeem_assets = list(generate_inner_transfer_assets(
        group[i + 4], filter=partial(is_transfer_receiver_non_zero_asset, wallet_address)))

    if len(redeem_assets) > 2:
        export_unknown(exporter, txinfo)
        return

    for asset in redeem_assets:
        if asset.id == send_asset_1.id:
            send_asset_1 -= asset
        elif asset.id == send_asset_2.id:
            send_asset_2 -= asset

    export_lp_deposit_tx(
        exporter, txinfo,
        send_asset_1, send_asset_2, lp_asset,
        fee_amount, COMMENT_ALGOFIV2, z_index)


def _handle_algofiv2_lend_lp_remove(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    i = 0
    while is_asset_optin(group[i]):
        i += 1

    lp_asset = get_transfer_asset(group[i])

    receive_asset_1 = get_inner_transfer_asset(group[i + 2],
                                               filter=partial(is_transfer_receiver, wallet_address))
    receive_asset_2 = get_inner_transfer_asset(group[i + 3],
                                               filter=partial(is_transfer_receiver, wallet_address))
    export_lp_withdraw_tx(
        exporter, txinfo,
        lp_asset, receive_asset_1, receive_asset_2,
        fee_amount, COMMENT_ALGOFIV2)


def _handle_algofiv2_pool_lp_remove(wallet_address, group, exporter, txinfo):
    fee_amount = get_fee_amount(wallet_address, group)

    i = 0
    while is_asset_optin(group[i]):
        i += 1

    lp_asset = get_transfer_asset(group[i])

    receive_assets = list(generate_inner_transfer_assets(group[i + 2],
                                                         filter=partial(is_transfer_receiver, wallet_address)))
    if len(receive_assets) != 2:
        export_unknown(exporter, txinfo)
        return

    export_lp_withdraw_tx(
        exporter, txinfo,
        lp_asset, receive_assets[0], receive_assets[1],
        fee_amount, COMMENT_ALGOFIV2)


def _handle_algofiv2_lend_zap(wallet_address, group, exporter, txinfo):
    i = 0
    while is_asset_optin(group[i]):
        i += 1

    _handle_algofiv2_lend_swap(wallet_address, group[:i + 5], exporter, txinfo, 0)
    _handle_algofiv2_lend_lp_add(wallet_address, group[i + 5:], exporter, txinfo, 1)


def _handle_algofiv2_pool_zap(wallet_address, group, exporter, txinfo):
    i = 0
    while is_asset_optin(group[i]):
        i += 1

    _handle_algofiv2_pool_swap(wallet_address, group[:i + 4], exporter, txinfo, 0)
    _handle_algofiv2_pool_lp_add(wallet_address, group[i + 4:], exporter, txinfo, 1)
