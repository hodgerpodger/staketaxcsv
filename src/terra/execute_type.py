import base64
import json
import logging

from terra import util_terra

EXECUTE_TYPE_UNKNOWN = "unknown_execute_type"
EXECUTE_TYPE_SWAP = "swap"
EXECUTE_TYPE_EXECUTE_SWAP_OPERATIONS = "execute_swap_operations"
EXECUTE_TYPE_EXECUTE_SWAP_OPERATIONS_IN_MSG = "execute_swap_operations_in_mg"
EXECUTE_TYPE_DEPOSIT_COLLATERAL = "deposit_collateral"
EXECUTE_TYPE_DEPOSIT_IDX = "deposit_idx"                 # deposit collateral for LP with "position_idx" field
EXECUTE_TYPE_DEPOSIT_IDX_IN_MSG = "deposit_idx_in_msg"   # deposit collateral for LP with "position_idx" field
EXECUTE_TYPE_DEPOSIT_STRATEGY_ID_IN_MSG = "deposit_strategy_id_in_msg"  # deposit collateral for LP (i.e. MINE-UST LP)
EXECUTE_TYPE_DEPOSIT_STABLE = "anchor_deposit"
EXECUTE_TYPE_DEPOSIT = "deposit"
EXECUTE_TYPE_REDEEM_STABLE = "anchor_withdraw"
EXECUTE_TYPE_CLAIM = "claim"
EXECUTE_TYPE_STAKE_VOTING_TOKENS = "stake_voting_tokens"
EXECUTE_TYPE_WITHDRAW_VOTING_TOKENS = "withdraw_toking_tokens"
EXECUTE_TYPE_WITHDRAW_VOTING_REWARDS = "withdraw_voting_rewards"
EXECUTE_TYPE_TRANSFER = "transfer"
EXECUTE_TYPE_INCREASE_ALLOWANCE = "increase_allowance"
EXECUTE_TYPE_BOND = "bond"
EXECUTE_TYPE_BOND_IN_MSG = "bond_in_msg"
EXECUTE_TYPE_UNBOND = "unbond"
EXECUTE_TYPE_UNBOND_IN_MSG = "unbond_in_msg"
EXECUTE_TYPE_WITHDRAW_LIQUIDITY = "withdraw_liquidity"
EXECUTE_TYPE_WITHDRAW = "withdraw"         # withdraw from Anchor LP Staking
EXECUTE_TYPE_WITHDRAW_IDX = "withdraw_idx"  # withdraw collateral for LP with "position_idx" field
EXECUTE_TYPE_WITHDRAW_FROM_STRATEGY = "withdraw_from_strategy"
EXECUTE_TYPE_CAST_VOTE = "cast_vote"
EXECUTE_TYPE_DEPOSIT_COLLATERAL = "deposit_collateral"
EXECUTE_TYPE_UNLOCK_COLLATERAL = "unlock_collateral"
EXECUTE_TYPE_CLAIM_REWARDS = "claim_rewards"
EXECUTE_TYPE_WITHDRAW = "withdraw"
EXECUTE_TYPE_BORROW_STABLE = "borrow_stable"
EXECUTE_TYPE_REPAY_STABLE = "repay_stable"
EXECUTE_TYPE_PROVIDE_LIQUIDITY = "provide_liquidity"
EXECUTE_TYPE_AUTO_STAKE = "auto_stake"
EXECUTE_TYPE_OPEN_POSITION = "open_position"
EXECUTE_TYPE_OPEN_POSITION_IN_MSG = "open_position_in_msg"
EXECUTE_TYPE_BURN = "burn"
EXECUTE_TYPE_WITHDRAW_UNBONDED = "withdraw_unbonded"
EXECUTE_TYPE_REGISTER = "register"
EXECUTE_TYPE_ASSERT_LIMIT_ORDER = "assert_limit_order"
EXECUTE_TYPE_ADD_WHITELIST = "add_whitelist"
EXECUTE_TYPE_ADD_MULTIPLE_USERS_TO_WHITE_LIST = "add_multiple_users_to_white_list"
EXECUTE_TYPE_RESERVE_NFT = "reserve_nft"
EXECUTE_TYPE_MINT_NFT = "mint_nft"
EXECUTE_TYPE_PURCHASE_NFT = "purchase_nft"
EXECUTE_TYPE_TRANSFER_NFT = "transfer_nft"
EXECUTE_TYPE_EXECUTE_ORDER = "execute_order"
EXECUTE_TYPE_APPROVE = "approve"
EXECUTE_TYPE_ADD_TO_WHITELIST = "add_to_whitelist"
EXECUTE_TYPE_ADD_TO_DEPOSIT = "add_to_deposit"
EXECUTE_TYPE_ACCEPT_DEPOSIT = "accept_deposit"
EXECUTE_TYPE_SEND_NFT = "send_nft"
EXECUTE_TYPE_AIRDROP = "airdrop"
EXECUTE_TYPE_ZAP_INTO_STRATEGY = "zap_into_strategy"
EXECUTE_TYPE_ZAP_OUT_OF_STRATEGY = "zap_out_of_strategy"


def _execute_type(elem, txinfo, index=0):
    txid = txinfo.txid
    execute_msg = util_terra._execute_msg(elem, index)

    if "send" in execute_msg:
        send = execute_msg["send"]
        msg = send.get("msg", None)
        if type(msg) == str:
            msg = json.loads(base64.b64decode(msg))

        if msg:
            if "execute_swap_operations" in msg:
                return EXECUTE_TYPE_EXECUTE_SWAP_OPERATIONS_IN_MSG
            if "redeem_stable" in msg:
                return EXECUTE_TYPE_REDEEM_STABLE
            if "swap" in msg:
                return EXECUTE_TYPE_SWAP
            if "stake_voting_tokens" in msg:
                return EXECUTE_TYPE_STAKE_VOTING_TOKENS
            if "bond" in msg:
                return EXECUTE_TYPE_BOND_IN_MSG
            if "unbond" in msg:
                return EXECUTE_TYPE_UNBOND_IN_MSG
            if "withdraw_liquidity" in msg:
                return EXECUTE_TYPE_WITHDRAW_LIQUIDITY
            if "deposit_collateral" in msg:
                return EXECUTE_TYPE_DEPOSIT_COLLATERAL
            if "burn" in msg:
                return EXECUTE_TYPE_BURN
            if "open_position" in msg:
                return EXECUTE_TYPE_OPEN_POSITION_IN_MSG
            if "deposit" in msg and "position_idx" in msg["deposit"]:
                return EXECUTE_TYPE_DEPOSIT_IDX_IN_MSG
            if "deposit" in msg and "strategy_id" in msg["deposit"]:
                return EXECUTE_TYPE_DEPOSIT_STRATEGY_ID_IN_MSG

    elif "claim" in execute_msg:
        return EXECUTE_TYPE_CLAIM
    elif "claim_rewards" in execute_msg:
        return EXECUTE_TYPE_CLAIM_REWARDS
    elif "swap" in execute_msg:
        return EXECUTE_TYPE_SWAP
    elif "deposit_stable" in execute_msg:
        return EXECUTE_TYPE_DEPOSIT_STABLE
    elif "deposit" in execute_msg:
        if "position_idx" in execute_msg["deposit"]:
            return EXECUTE_TYPE_DEPOSIT_IDX
        else:
            return EXECUTE_TYPE_DEPOSIT
    elif "withdraw_voting_tokens" in execute_msg:
        return EXECUTE_TYPE_WITHDRAW_VOTING_TOKENS
    elif "withdraw_voting_rewards" in execute_msg:
        return EXECUTE_TYPE_WITHDRAW_VOTING_REWARDS
    elif "transfer" in execute_msg:
        return EXECUTE_TYPE_TRANSFER
    elif "provide_liquidity" in execute_msg:
        return EXECUTE_TYPE_PROVIDE_LIQUIDITY
    elif "increase_allowance" in execute_msg:
        return _execute_type(elem, txinfo, index + 1)
    elif "bond" in execute_msg:
        return EXECUTE_TYPE_BOND
    elif "unbond" in execute_msg:
        return EXECUTE_TYPE_UNBOND
    elif "withdraw" in execute_msg:
        if "position_idx" in execute_msg["withdraw"]:
            return EXECUTE_TYPE_WITHDRAW_IDX
        else:
            return EXECUTE_TYPE_WITHDRAW
    elif "execute_swap_operations" in execute_msg:
        return EXECUTE_TYPE_EXECUTE_SWAP_OPERATIONS
    elif "cast_vote" in execute_msg:
        return EXECUTE_TYPE_CAST_VOTE
    elif "borrow_stable" in execute_msg:
        return EXECUTE_TYPE_BORROW_STABLE
    elif "repay_stable" in execute_msg:
        return EXECUTE_TYPE_REPAY_STABLE
    elif "unlock_collateral" in execute_msg:
        return EXECUTE_TYPE_UNLOCK_COLLATERAL
    elif "auto_stake" in execute_msg:
        return EXECUTE_TYPE_AUTO_STAKE
    elif "open_position" in execute_msg:
        return EXECUTE_TYPE_OPEN_POSITION
    elif "withdraw_unbonded" in execute_msg:
        return EXECUTE_TYPE_WITHDRAW_UNBONDED
    elif "register" in execute_msg:
        return EXECUTE_TYPE_REGISTER
    elif "assert_limit_order" in execute_msg:
        return EXECUTE_TYPE_ASSERT_LIMIT_ORDER
    elif "withdraw_from_strategy" in execute_msg:
        return EXECUTE_TYPE_WITHDRAW_FROM_STRATEGY
    elif "add_whitelist" in execute_msg:
        return EXECUTE_TYPE_ADD_WHITELIST
    elif "add_to_whitelist" in execute_msg:
        return EXECUTE_TYPE_ADD_TO_WHITELIST
    elif "add_to_deposit" in execute_msg:
        return EXECUTE_TYPE_ADD_TO_DEPOSIT
    elif "accept_deposit" in execute_msg:
        return EXECUTE_TYPE_ACCEPT_DEPOSIT
    elif "reserve_nft" in execute_msg:
        return EXECUTE_TYPE_RESERVE_NFT
    elif "add_multiple_users_to_white_list" in execute_msg:
        return EXECUTE_TYPE_ADD_MULTIPLE_USERS_TO_WHITE_LIST
    elif "mint_nft" in execute_msg:
        return EXECUTE_TYPE_MINT_NFT
    elif "purchase_nft" in execute_msg:
        return EXECUTE_TYPE_PURCHASE_NFT
    elif "execute_order" in execute_msg:
        return EXECUTE_TYPE_EXECUTE_ORDER
    elif "transfer_nft" in execute_msg:
        return EXECUTE_TYPE_TRANSFER_NFT
    elif "send_nft" in execute_msg:
        return EXECUTE_TYPE_SEND_NFT
    elif "approve" in execute_msg:
        return EXECUTE_TYPE_APPROVE
    elif "airdrop" in execute_msg:
        return EXECUTE_TYPE_AIRDROP
    elif "zap_into_strategy" in execute_msg:
        return EXECUTE_TYPE_ZAP_INTO_STRATEGY
    elif "zap_out_of_strategy" in execute_msg:
        return EXECUTE_TYPE_ZAP_OUT_OF_STRATEGY

    logging.error("Unable to determine execute type for txid=%s", txid, extra={
        "txid": txid,
        "execute_msg": execute_msg
    })
    return EXECUTE_TYPE_UNKNOWN
