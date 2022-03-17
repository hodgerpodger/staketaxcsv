import logging

import terra.execute_type as ex
from common.ErrorCounter import ErrorCounter
from common.ExporterTypes import (
    TX_TYPE_LOTA_UNKNOWN, TX_TYPE_SPEC_UNKNOWN, TX_TYPE_ASTROPORT_UNKNOWN, TX_TYPE_DISTRIBUTE,
    TX_TYPE_VOTE,
)
from terra import util_terra
from terra.constants import (
    CONTRACT_RANDOMEARTH,
    CONTRACTS_LOTA,
    CONTRACTS_SPEC,
    CONTRACTS_ASTROPORT,
    CONTRACTS_PYLON,
    CONTRACTS_APOLLO,
    CONTRACTS_LOOP,
    CONTRACTS_MIRROR,
)
from terra.col4.handle_simple import handle_simple, handle_unknown_detect_transfers

from terra.col4 import (
    handle_anchor_bond,
    handle_anchor_borrow,
    handle_anchor_earn,
    handle_anchor_liquidate,
    handle_governance,
    handle_loop,
    handle_mirror_borrow,
    handle_lp,
    handle_randomearth,
    handle_reward_contract,
    handle_reward_pylon,
    handle_spec,
    handle_swap,
    handle_transfer,
    handle_zap,
    handle_mirror,
)

# execute_type -> tx_type mapping for generic transactions with no tax details
EXECUTE_TYPES_SIMPLE = {
    ex.EXECUTE_TYPE_CAST_VOTE: TX_TYPE_VOTE,
    ex.EXECUTE_TYPE_REGISTER: TX_TYPE_LOTA_UNKNOWN,
}


def handle(exporter, elem, txinfo):
    txid = elem["txhash"]
    contract = util_terra._contract(elem, 0)
    execute_type = ex._execute_type(elem, txinfo)

    # ######### Handle by specific contract ###########################################

    # Handle dApp contracts as _{DAPP}_unknown
    if util_terra._any_contracts(CONTRACTS_LOTA, elem):
        return handle_simple(exporter, txinfo, TX_TYPE_LOTA_UNKNOWN)
    elif util_terra._any_contracts(CONTRACTS_SPEC, elem):
        if execute_type == ex.EXECUTE_TYPE_MINT_COLLATERAL:
            return handle_spec.handle_spec_withdraw(exporter, elem, txinfo)
        elif execute_type == ex.EXECUTE_TYPE_BOND:
            return handle_lp.handle_lp_deposit(exporter, elem, txinfo)
        elif execute_type == ex.EXECUTE_TYPE_UNBOND:
            return handle_lp.handle_lp_withdraw(exporter, elem, txinfo)
        else:
            return handle_simple(exporter, txinfo, TX_TYPE_SPEC_UNKNOWN)
    elif util_terra._any_contracts(CONTRACTS_ASTROPORT, elem):
        return handle_simple(exporter, txinfo, TX_TYPE_ASTROPORT_UNKNOWN)
    elif util_terra._any_contracts(CONTRACTS_PYLON, elem):
        if execute_type == ex.EXECUTE_TYPE_WITHDRAW:
            return handle_reward_pylon.handle_pylon_withdraw(exporter, elem, txinfo)
        else:
            return handle_unknown_detect_transfers(exporter, txinfo, elem)
    elif contract == CONTRACT_RANDOMEARTH:
        return handle_randomearth.handle_randomearth(exporter, elem, txinfo)
    elif util_terra._any_contracts(CONTRACTS_APOLLO, elem):
        return handle_reward_contract.handle_airdrop(exporter, elem, txinfo)
    elif util_terra._any_contracts(CONTRACTS_LOOP, elem):
        return handle_loop.handle_unstake_and_claim(exporter, elem, txinfo)
    elif util_terra._any_contracts(CONTRACTS_MIRROR, elem):
        if execute_type == ex.EXECUTE_TYPE_SUBMIT_ORDER:
            return handle_mirror.handle_submit_limit_order(exporter, elem, txinfo)


    # ########## Handle by execute_msg data keys ######################################

    # General
    elif execute_type in EXECUTE_TYPES_SIMPLE:
        tx_type = EXECUTE_TYPES_SIMPLE[execute_type]
        return handle_simple(exporter, txinfo, tx_type)
    elif execute_type == ex.EXECUTE_TYPE_CLAIM:
        return handle_reward_contract.handle_airdrop(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_TRANSFER:
        # Currently handles transfer to/from shuttle bridge
        return handle_transfer.handle_transfer_contract(exporter, elem, txinfo)

    # nft transactions
    elif execute_type in (ex.EXECUTE_TYPE_ADD_WHITELIST,
                          ex.EXECUTE_TYPE_ADD_MULTIPLE_USERS_TO_WHITE_LIST,
                          ex.EXECUTE_TYPE_ADD_TO_WHITELIST):
        return handle_randomearth.handle_add_whitelist(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_ADD_TO_DEPOSIT:
        return handle_randomearth.handle_add_to_deposit(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_ACCEPT_DEPOSIT:
        return handle_randomearth.handle_accept_deposit(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_RESERVE_NFT:
        return handle_randomearth.handle_reserve_nft(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_MINT_NFT:
        return handle_randomearth.handle_mint_nft(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_PURCHASE_NFT:
        return handle_randomearth.handle_purchase_nft(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_EXECUTE_ORDER:
        return handle_randomearth.handle_execute_order(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_POST_ORDER:
        return handle_randomearth.handle_post_order(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_TRANSFER_NFT:
        return handle_randomearth.handle_transfer_nft(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_SEND_NFT:
        return handle_randomearth.handle_send_nft(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_APPROVE:
        return handle_randomearth.handle_approve(exporter, elem, txinfo)

    # Swaps
    elif execute_type == ex.EXECUTE_TYPE_SWAP:
        return handle_swap.handle_swap(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_EXECUTE_SWAP_OPERATIONS:
        return handle_swap.handle_execute_swap_operations(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_EXECUTE_SWAP_OPERATIONS_IN_MSG:
        return handle_swap.handle_execute_swap_operations(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_ASSERT_LIMIT_ORDER:
        return handle_swap.handle_swap_msgswap(exporter, elem, txinfo)

    # Governance staking for ANC or MIR or VKR
    elif execute_type == ex.EXECUTE_TYPE_STAKE_VOTING_TOKENS:
        return handle_governance.handle_governance_stake(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_VOTING_TOKENS:
        return handle_governance.handle_governance_unstake(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_VOTING_REWARDS:
        return handle_governance.handle_governance_reward(exporter, elem, txinfo)

    # Anchor Borrow Transactions
    elif execute_type == ex.EXECUTE_TYPE_BORROW_STABLE:
        return handle_anchor_borrow.handle_borrow(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_REPAY_STABLE:
        return handle_anchor_borrow.handle_repay(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_DEPOSIT_COLLATERAL:
        return handle_anchor_borrow.handle_deposit_collateral(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_UNLOCK_COLLATERAL:
        return handle_anchor_borrow.handle_withdraw_collateral(exporter, elem, txinfo)

    # Anchor Liquidate Transactions
    elif execute_type == ex.EXECUTE_TYPE_LIQUIDATE_COLLATERAL:
        return handle_anchor_liquidate.handle_liquidate(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_SUBMIT_BID:
        return handle_anchor_liquidate.handle_submit_bid(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_RETRACT_BID:
        return handle_anchor_liquidate.handle_retract_bid(exporter, elem, txinfo)

    # Anchor Bond transactions
    elif execute_type == ex.EXECUTE_TYPE_BOND:
        return handle_anchor_bond.handle_bond(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_UNBOND_IN_MSG:
        return handle_anchor_bond.handle_unbond(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_UNBONDED:
        return handle_anchor_bond.handle_unbond_withdraw(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_BURN_COLLATERAL:
        return handle_anchor_bond.handle_burn_collateral(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_MINT_COLLATERAL:
        return handle_anchor_bond.handle_mint_collateral(exporter, elem, txinfo)

    # Mirror Borrow Transactions
    elif execute_type in [ex.EXECUTE_TYPE_OPEN_POSITION, ex.EXECUTE_TYPE_OPEN_POSITION_IN_MSG]:
        return handle_mirror_borrow.handle_deposit_borrow(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_BURN:
        return handle_mirror_borrow.handle_repay_withdraw(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_AUCTION:
        return handle_mirror_borrow.handle_auction(exporter, elem, txinfo)

    # Mirror LP transactions
    elif execute_type == ex.EXECUTE_TYPE_PROVIDE_LIQUIDITY:
        return handle_lp.handle_lp_deposit(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_LIQUIDITY:
        return handle_lp.handle_lp_withdraw(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_BOND_IN_MSG:
        return handle_lp.handle_lp_stake(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_DEPOSIT_STRATEGY_ID_IN_MSG:
        return handle_lp.handle_lp_stake_deposit_strategy(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_UNBOND:
        return handle_lp.handle_lp_unstake(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_FROM_STRATEGY:
        return handle_lp.handle_lp_unstake_withdraw_from_strategy(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_AUTO_STAKE:
        return handle_lp.handle_lp_long_farm(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_WITHDRAW_IDX:
        return handle_lp.handle_lp_withdraw_idx(exporter, elem, txinfo)
    elif execute_type in [ex.EXECUTE_TYPE_DEPOSIT_IDX, ex.EXECUTE_TYPE_DEPOSIT_IDX_IN_MSG]:
        return handle_lp.handle_lp_deposit_idx(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_DISTRIBUTE:
        return handle_lp.handle_simple(exporter, txinfo, TX_TYPE_DISTRIBUTE)

    # Anchor Earn transactions
    elif execute_type in [ex.EXECUTE_TYPE_DEPOSIT_STABLE, ex.EXECUTE_TYPE_DEPOSIT]:
        return handle_anchor_earn.handle_anchor_earn_deposit(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_REDEEM_STABLE:
        return handle_anchor_earn.handle_anchor_earn_withdraw(exporter, elem, txinfo)

    # Contract reward transactions
    elif execute_type == ex.EXECUTE_TYPE_CLAIM_REWARDS:
        return handle_reward_contract.handle_reward_contract(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_WITHDRAW and contract in handle_reward_contract.CONTRACTS_WITHDRAW_REWARD:
        return handle_reward_contract.handle_reward_contract(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_AIRDROP:
        return handle_reward_pylon.handle_airdrop_pylon(exporter, elem, txinfo)

    # Apollo
    elif execute_type == ex.EXECUTE_TYPE_ZAP_INTO_STRATEGY:
        return handle_zap.handle_zap_into_strategy(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_ZAP_OUT_OF_STRATEGY:
        return handle_zap.handle_zap_out_of_strategy(exporter, elem, txinfo)

    # Astroport
    elif execute_type == ex.EXECUTE_TYPE_INCREASE_LOCKUP:
        return handle_lp.handle_lp_stake(exporter, elem, txinfo)

    # Bridge transfers
    elif execute_type == ex.EXECUTE_TYPE_DEPOSIT_TOKENS:
        # wormhole bridge: transfer out
        return handle_transfer.handle_transfer_bridge_wormhole(exporter, elem, txinfo)
    elif execute_type == ex.EXECUTE_TYPE_SUBMIT_VAA:
        # wormhole bridge: transfer in
        return handle_transfer.handle_transfer_bridge_wormhole(exporter, elem, txinfo)

    else:
        logging.error("Unknown execute_type for txid=%s", txid)
        ErrorCounter.increment("unknown_execute_type", txid)
        handle_unknown_detect_transfers(exporter, txinfo, elem)
