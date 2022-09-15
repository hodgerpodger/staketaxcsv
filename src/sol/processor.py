import logging

from staketaxcsv.common.ErrorCounter import ErrorCounter
from staketaxcsv.sol import constants as co
from staketaxcsv.sol.config_sol import localconfig
from staketaxcsv.sol.handle_account_misc import (
    handle_close_account_tx,
    handle_init_account_tx,
    is_close_account_tx,
    is_init_account_tx,
)
from staketaxcsv.sol.handle_jupiter import handle_jupiter_aggregator_v2
from staketaxcsv.sol.handle_marinade import handle_marinade
from staketaxcsv.sol.handle_metaplex import handle_metaplex, handle_nft_mint, is_nft_mint
from staketaxcsv.sol.handle_nft_market import get_nft_program, handle_nft_exchange
from staketaxcsv.sol.handle_notimestamp import handle_notimestamp_tx, is_notimestamp_tx
from staketaxcsv.sol.handle_orca import handle_orca_swap_v2
from staketaxcsv.sol.handle_raydium_lp import handle_raydium_lp_v2, handle_raydium_lp_v3, handle_raydium_lp_v4
from staketaxcsv.sol.handle_raydium_stake import handle_raydium_stake, handle_raydium_stake_v4, handle_raydium_stake_v5
from staketaxcsv.sol.handle_saber import handle_saber, handle_saber_farm_ssf, handle_saber_stable_swap
from staketaxcsv.sol.handle_serumv3 import handle_serumv3
from staketaxcsv.sol.handle_simple import (
    handle_simple_tx,
    handle_unknown,
    handle_unknown_detect_transfers,
    is_simple_tx,
)
from staketaxcsv.sol.handle_swap_v2 import handle_program_swap_v2
from staketaxcsv.sol.handle_transfer import handle_transfer, is_transfer
from staketaxcsv.sol.handle_unknowns import handle_2kd, handle_djv
from staketaxcsv.sol.handle_vote import handle_vote
from staketaxcsv.sol.handle_wormhole import handle_wormhole
from staketaxcsv.sol.parser import parse_tx


def process_tx(wallet_info, exporter, txid, data):
    txinfo = parse_tx(txid, data, wallet_info)

    try:
        if not txinfo:
            return
        program_ids = txinfo.program_ids

        if is_notimestamp_tx(txinfo):
            handle_notimestamp_tx(exporter, txinfo)

        # Bridges
        elif co.PROGRAMID_WORMHOLE in program_ids or co.PROGRAMID_WORMHOLE2 in program_ids:
            handle_wormhole(exporter, txinfo)

        # Serum programs
        elif co.PROGRAMID_SWAP_V2 in program_ids:
            handle_program_swap_v2(exporter, txinfo)
        elif co.PROGRAMID_SERUM_V3 in program_ids:
            handle_serumv3(exporter, txinfo)

        # Marinade Finance
        elif co.PROGRAMID_MARINADE in program_ids:
            handle_marinade(exporter, txinfo)

        # Unknown programs
        elif co.PROGRAMID_UNKNOWN_DJV in program_ids:
            handle_djv(exporter, txinfo)
        elif co.PROGRAMID_UNKNOWN_2KD in program_ids:
            handle_2kd(exporter, txinfo)

        # Raydium programs
        elif co.PROGRAMID_RAYDIUM_LP_V2 in program_ids:
            handle_raydium_lp_v2(exporter, txinfo)
        elif co.PROGRAMID_RAYDIUM_LP_V3 in program_ids:
            handle_raydium_lp_v3(exporter, txinfo)
        elif co.PROGRAMID_RAYDIUM_LP_V4 in program_ids:
            handle_raydium_lp_v4(exporter, txinfo)
        elif co.PROGRAMID_RAYDIUM_STAKE in program_ids:
            handle_raydium_stake(exporter, txinfo)
        elif co.PROGRAMID_RAYDIUM_STAKE_V4 in program_ids:
            handle_raydium_stake_v4(exporter, txinfo)
        elif co.PROGRAMID_RAYDIUM_STAKE_V5 in program_ids:
            handle_raydium_stake_v5(exporter, txinfo)

        # Orca programs
        elif co.PROGRAMID_ORCA_SWAP_V2 in program_ids or co.PROGRAMID_ORCA_SWAP_WHIRL in program_ids:
            handle_orca_swap_v2(exporter, txinfo)

        # Saber programs
        elif co.PROGRAMID_SABER in program_ids:
            handle_saber(exporter, txinfo)
        elif co.PROGRAMID_SABER_STABLE_SWAP in program_ids:
            handle_saber_stable_swap(exporter, txinfo)
        elif co.PROGRAMID_SABER_FARM_SSF in program_ids:
            handle_saber_farm_ssf(exporter, txinfo)

        # Jupiter Aggregator
        elif co.PROGRAMID_JUPITER_AGGREGATOR_V2 in program_ids:
            handle_jupiter_aggregator_v2(exporter, txinfo)

        # Metaplex NFT Candy Machinine program
        elif co.PROGRAMID_METAPLEX_CANDY in program_ids:
            handle_metaplex(exporter, txinfo)

        # NFT marketplace transactions
        elif get_nft_program(txinfo):
            handle_nft_exchange(exporter, txinfo)

        # NFT transactions
        elif is_nft_mint(txinfo):
            handle_nft_mint(exporter, txinfo)

        # Other
        elif co.PROGRAMID_VOTE in program_ids:
            handle_vote(exporter, txinfo)
        elif is_simple_tx(txinfo):
            handle_simple_tx(exporter, txinfo)
        elif is_init_account_tx(txinfo):
            handle_init_account_tx(exporter, txinfo)
        elif is_transfer(txinfo):
            handle_transfer(exporter, txinfo)
        elif is_close_account_tx(txinfo):
            handle_close_account_tx(exporter, txinfo)

        else:
            handle_unknown_detect_transfers(exporter, txinfo)
            ErrorCounter.increment("unknown_sol_tx", txid)

    except Exception as e:
        logging.error("Exception when handling txid=%s, exception=%s", txid, str(e))
        ErrorCounter.increment("exception", txid)
        handle_unknown(exporter, txinfo)

        if localconfig.debug:
            raise e

    return txinfo
