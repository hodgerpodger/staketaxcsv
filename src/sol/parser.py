"""
Data parsing functions applicable to all transactions
"""

import logging
import re
from datetime import datetime, timezone

from sol import util_sol
from sol.api_rpc import RpcAPI
from sol.constants import BILLION, CURRENCY_SOL, INSTRUCTION_TYPE_DELEGATE, MINT_SOL, PROGRAM_STAKE
from sol.tickers.tickers import Tickers
from sol.TxInfoSol import TxInfoSol
from sol.handle_transfer import is_transfer
import sol.util_sol


def parse_tx(txid, data, wallet_info):
    """ Parses data returned by RcpAPI.fetch_tx().  Returns TxInfoSol object """
    wallet_address = wallet_info.wallet_address
    result = data.get("result", None)

    # Handle old transaction where api fails.  Return transaction with just txid, nothing else.
    if result is None:
        logging.warning("Unable to fetch txid=%s.  Probably old transaction where api "
                        "fails.", txid)
        txinfo = TxInfoSol(txid, "", "", wallet_address)
        return txinfo

    # Handle old transaction where timestamp missing (something like before 12/2020)
    if not result.get("blockTime"):
        logging.warning("Detected timestamp missing for txid=%s.  Probably old transaction", txid)
        txinfo = TxInfoSol(txid, "", "", wallet_address)
        return txinfo

    # Transactions that resulted in error
    meta = result["meta"]
    if meta is None:
        logging.error("empty meta field.  txid=%s", txid)
        return None
    err = result["meta"]["err"]
    if err is not None:
        return None

    ts = result["blockTime"]
    timestamp = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if ts else ""
    fee = ""
    instructions = data["result"]["transaction"]["message"]["instructions"]

    txinfo = TxInfoSol(txid, timestamp, fee, wallet_address)

    txinfo.fee_blockchain = float(result["meta"]["fee"]) / BILLION
    txinfo.instructions = instructions
    txinfo.instruction_types = _instruction_types(instructions)
    txinfo.program_ids = [x["programId"] for x in txinfo.instructions]
    txinfo.input_accounts = _input_accounts(instructions)

    txinfo.inner = _extract_inner_instructions(data)
    txinfo.inner_parsed = _parsed(txinfo.inner)

    txinfo.log_instructions, txinfo.log, txinfo.log_string = _log_messages(txid, data)

    txinfo.wallet_accounts = _wallet_accounts(txid, wallet_address, txinfo.instructions, txinfo.inner)
    txinfo.account_to_mint, txinfo.mints = _mints(data, wallet_address)

    txinfo.balance_changes_all, txinfo.balance_changes_wallet = _balance_changes(data, txinfo.wallet_accounts, txinfo.mints)
    txinfo.transfers = _transfers(txinfo.balance_changes_wallet)

    txinfo.transfers_net, txinfo.fee = _transfers_net(txinfo, txinfo.transfers, fee)

    if _has_empty_token_balances(data, txinfo.mints):
        # Fall back to alternative method to calculate transfers
        if is_transfer(txinfo):
            txinfo.transfers = _transfers_instruction(txinfo, txinfo.instructions)
            txinfo.transfers_net, _ = _transfers_net(txinfo, txinfo.transfers, fee, mint_to=True)

    txinfo.lp_transfers = _transfers_instruction(txinfo, txinfo.inner)
    txinfo.lp_transfers_net, txinfo.lp_fee = _transfers_net(
        txinfo, txinfo.lp_transfers, txinfo.fee, mint_to=True)

    # Update wallet_info with any staking addresses found
    addresses = _staking_addresses_found(wallet_address, txinfo.instructions)
    for address in addresses:
        wallet_info.add_staking_address(address)

    return txinfo


def _staking_addresses_found(wallet_address, instructions):
    out = []
    for instruction in instructions:
        parsed = instruction.get("parsed", None)
        instruction_type = parsed.get("type", None) if (parsed and type(parsed) is dict) else None
        program = instruction.get("program")

        if (program == PROGRAM_STAKE and instruction_type == INSTRUCTION_TYPE_DELEGATE):
            stake_account = parsed["info"]["stakeAccount"]
            stake_authority = parsed["info"]["stakeAuthority"]
            if stake_authority == wallet_address:
                out.append(stake_account)

    return out


def _has_empty_token_balances(data, mints):
    post_token_balances = data["result"]["meta"]["postTokenBalances"]
    pre_token_balances = data["result"]["meta"]["preTokenBalances"]

    if len(post_token_balances) == 0 and len(pre_token_balances) == 0 and len(mints.keys()) > 1:
        return True
    else:
        return False


def _transfers(balance_changes):
    transfers_in = []
    transfers_out = []

    for account_address, (currency, amount_change) in balance_changes.items():
        if amount_change > 0:
            transfers_in.append((amount_change, currency, "", account_address))
        elif amount_change < 0:
            transfers_out.append((-amount_change, currency, account_address, ""))

    return transfers_in, transfers_out, []


def _balance_changes(data, wallet_accounts, mints):
    balance_changes_sol = _balance_changes_sol(data)
    balance_changes_tokens = _balance_changes_tokens(data, mints)

    balance_changes = dict(balance_changes_sol)
    balance_changes.update(dict(balance_changes_tokens))

    balance_changes_wallet = {k: v for (k, v) in balance_changes.items() if k in wallet_accounts}
    return balance_changes, balance_changes_wallet


def _balance_changes_tokens(data, mints):
    account_keys = [row["pubkey"] for row in data["result"]["transaction"]["message"]["accountKeys"]]

    post_token_balances = data["result"]["meta"]["postTokenBalances"]
    pre_token_balances = data["result"]["meta"]["preTokenBalances"]

    a = {}
    b = {}
    balance_changes = {}
    for row in pre_token_balances:
        account_address, currency_a, amount_a, _ = _row_to_amount_currency(row, account_keys, mints)
        a[account_address] = (currency_a, amount_a)

    for row in post_token_balances:
        account_address, currency_b, amount_b, decimals = _row_to_amount_currency(row, account_keys, mints)
        b[account_address] = (currency_b, amount_b)

        # calculate change in balance
        currency_a, amount_a = a.get(account_address, (currency_b, 0.0))
        amount_change = round(amount_b - amount_a, decimals)

        # add to result
        balance_changes[account_address] = (currency_a, amount_change)

    # Handle case where post_token_balance doesn't exist for token (aka zero balance)
    for row in pre_token_balances:
        account_address, currency_a, amount_a, _ = _row_to_amount_currency(row, account_keys, mints)
        if account_address not in balance_changes:
            balance_changes[account_address] = (currency_a, -amount_a)

    return balance_changes


def _row_to_amount_currency(row, account_keys, mints):
    account_address = account_keys[row["accountIndex"]]
    mint = row["mint"]
    amount = row["uiTokenAmount"]["uiAmount"]
    decimals = row["uiTokenAmount"]["decimals"]
    if not amount:
        amount = 0.0
    currency = mints[mint]["currency"] if mint in mints else mint

    return account_address, currency, amount, decimals


def _balance_changes_sol(data):
    account_keys = [row["pubkey"] for row in data["result"]["transaction"]["message"]["accountKeys"]]

    post_balances_sol = data["result"]["meta"]["postBalances"]
    pre_balances_sol = data["result"]["meta"]["preBalances"]

    balance_changes = {}
    for i, account_address in enumerate(account_keys):
        amount = (float(post_balances_sol[i]) - float(pre_balances_sol[i])) / BILLION
        amount = round(amount, 9)
        if amount != 0:
            balance_changes[account_address] = (CURRENCY_SOL, amount)

    return balance_changes


def _wallet_accounts(txid, wallet_address, instructions, inner):
    token_accounts = RpcAPI.fetch_token_accounts(wallet_address)
    accounts_wallet = set(token_accounts.keys())

    accounts_instruction = _instruction_accounts(txid, wallet_address, instructions, inner)

    accounts = set(accounts_instruction)
    accounts = accounts.union(accounts_wallet)
    return accounts


def _instruction_types(instructions):
    out = []
    for instruction in instructions:
        parsed = instruction.get("parsed", None)
        instruction_type = parsed.get("type", None) if (parsed and type(parsed) is dict) else None
        program = instruction.get("program")
        out.append((instruction_type, program))
    return out


def _input_accounts(instructions):
    out = []
    for instruction in instructions:
        if "accounts" in instruction:
            out.append(instruction["accounts"])
    return out


def _mints(data, wallet_address):
    """ Returns
    account_to_mints: dict of <account_address> -> <mint_address>
    mints: dict of <mint_address> -> { "currency" : <ticker>, "decimals" : <decimals> }
    """

    # ## Get mints of wallet token accounts
    token_accounts = RpcAPI.fetch_token_accounts(wallet_address)
    out = dict(token_accounts)

    # ## Get mints of accounts found in preTokenBalances and postTokenBalances

    # Get account addresses
    accounts = [d["pubkey"] for d in data["result"]["transaction"]["message"]["accountKeys"]]

    # Get accounts of mints found in preTokenBalances and postTokenBalances
    mintlist = list(data["result"]["meta"]["preTokenBalances"])
    mintlist.extend(list(data["result"]["meta"]["postTokenBalances"]))
    for info in mintlist:
        account_index = info["accountIndex"]
        mint = info["mint"]
        decimals = info["uiTokenAmount"]["decimals"]

        account = accounts[account_index]
        out[account] = {
            "mint": mint,
            "decimals": decimals
        }

    # ## Repackage output format
    account_to_mint = {}
    mints = {}
    for account_address, info in out.items():
        mint = info["mint"]
        decimals = info["decimals"]

        account_to_mint[account_address] = mint
        mints[mint] = {
            "currency": Tickers.get(mint),
            "decimals": decimals
        }

    # Add wallet_address
    account_to_mint[wallet_address] = MINT_SOL
    mints[MINT_SOL] = {
        "currency": CURRENCY_SOL,
        "decimals": 9
    }

    return account_to_mint, mints


def _extract_inner_instructions(data):
    if "innerInstructions" not in data["result"]["meta"]:
        return None
    inner_instructions = data["result"]["meta"]["innerInstructions"]
    if inner_instructions is None:
        return None

    out = []
    for instructions_dict in inner_instructions:
        if "instructions" in instructions_dict:
            out.extend(instructions_dict["instructions"])

    return out


def _parsed(inner_instructions):
    out = {}

    for elem in inner_instructions:
        if "parsed" in elem:
            parsed = elem["parsed"]
            info = parsed["info"]
            type = parsed["type"]

            if type not in out:
                out[type] = []
            out[type].append(info)

    return out


def _instruction_accounts(txid, wallet_address, instructions, inner):
    accounts = set()
    accounts.add(wallet_address)
    instrs = instructions[:] + inner[:]

    # Add associated accounts from Instructions
    for instruction in instrs:
        if "parsed" in instruction:
            parsed = instruction["parsed"]
            if type(parsed) is dict:
                # if wallet associated with source
                if parsed.get("type") in ["initializeAccount", "approve", "transfer", "transferChecked"]:
                    info = parsed["info"]

                    # Grab set of addresses associated with source
                    keys = ["authority", "source", "newAccount", "owner", "account"]
                    addresses_source = set([info.get(k) for k in keys if k in info])
                    # Don't include token program address
                    addresses_source = set([x for x in addresses_source if not x.startswith("Token")])

                    if accounts.intersection(addresses_source):
                        accounts = accounts.union(addresses_source)

                # if wallet associated with destination
                if parsed.get("type") == "closeAccount":
                    info = parsed["info"]
                    account = info["account"]
                    destination = info["destination"]

                    if destination == wallet_address:
                        accounts.add(account)

    return accounts


def _transfers_instruction(txinfo, instructions):
    """ Returns transfers using information from instructions data (alternative method instead of balance changes) """
    txid = txinfo.txid
    account_to_mint = txinfo.account_to_mint
    wallet_accounts = txinfo.wallet_accounts
    wallet_address = txinfo.wallet_address

    transfers_in = []
    transfers_out = []
    transfers_unknown = []

    for i, instruction in enumerate(instructions):
        if "parsed" in instruction:
            parsed = instruction["parsed"]
            if type(parsed) is dict and parsed.get("type") == "transfer":
                info = parsed["info"]

                amount_string = info.get("amount", None)
                lamports = info.get("lamports", None)
                token_amount = info.get("tokenAmount", None)
                authority = info.get("authority", None)
                source = info.get("source", None)
                destination = info.get("destination", None)

                # self transfer
                if source and source == destination:
                    continue
                if amount_string == "0":
                    continue

                # Determine amount
                if amount_string is not None:
                    pass
                elif lamports is not None:
                    amount_string = lamports
                elif token_amount is not None:
                    amount_string = token_amount["amount"]

                # Determine mint
                if lamports:
                    mint = MINT_SOL
                elif source in account_to_mint and account_to_mint[source] != MINT_SOL:
                    mint = account_to_mint[source]
                elif destination in account_to_mint and account_to_mint[destination] != MINT_SOL:
                    mint = account_to_mint[destination]
                else:
                    mint = MINT_SOL

                # Determine amount, currency
                amount, currency = util_sol.amount_currency(txinfo, amount_string, mint)

                # Determine direction of transfer
                if source in wallet_accounts:
                    transfers_out.append((amount, currency, wallet_address, destination))
                elif authority in wallet_accounts:
                    transfers_out.append((amount, currency, wallet_address, destination))
                elif destination in wallet_accounts:
                    transfers_in.append((amount, currency, source, destination))
                else:
                    logging.error("Unable to determine direction for info: %s", info)
                    transfers_unknown.append((amount, currency, source, destination))

    return transfers_in, transfers_out, transfers_unknown


def _extract_mint_to(instructions, wallet_address):
    try:
        for instruction in instructions:
            parsed = instruction.get("parsed", None)
            if parsed and parsed.get("type") == "mintTo":
                info = parsed["info"]
                amount = info["amount"]
                mint = info["mint"]

                return amount, mint

    except Exception:
        pass
    return None, None


def _add_mint_to_as_transfers(txinfo, net_transfers_in):
    """ Adds 'mintTo' instructions as transfers if found """

    # Extract any "mintTo" from instructions
    mint_amount_string, mint = _extract_mint_to(txinfo.instructions, txinfo.wallet_address)

    # Extract any "mintTo" from inner instructions
    if not mint:
        mint_amount_string, mint = _extract_mint_to(txinfo.inner, txinfo.wallet_address)

    if mint_amount_string and mint:
        mints_transfers_in = [x[1] for x in net_transfers_in]
        amount, currency = util_sol.amount_currency(txinfo, mint_amount_string, mint)

        if mint in mints_transfers_in:
            # Mint transaction already reflected as inbound transfer.  Do nothing
            pass
        else:
            net_transfers_in.append((amount, currency, "", ""))


def _transfers_net(txinfo, transfers, fee, mint_to=False):
    """ Combines like currencies and removes fees from transfers lists """
    _transfers_in, _transfers_out, _transfers_unknown = transfers

    transfers_in, transfers_out, fee = util_sol.detect_fees(_transfers_in, _transfers_out, fee)

    # Sum up net transfer by currency, into a dict
    net_amounts = {}
    for amount, currency, source, destination in transfers_in:
        if currency not in net_amounts:
            net_amounts[currency] = 0
        net_amounts[currency] += amount
    for amount, currency, source, destination in transfers_out:
        if currency not in net_amounts:
            net_amounts[currency] = 0
        net_amounts[currency] -= amount

    # Convert dict into two lists of transactions, net_transfers_in and net_transfers_out
    net_transfers_in = []
    net_transfers_out = []
    for currency, amount in net_amounts.items():
        if amount < 0:
            source, destination = _get_source_destination(currency, False, transfers_in, transfers_out)
            net_transfers_out.append((-amount, currency, source, destination))
        elif amount > 0:
            source, destination = _get_source_destination(currency, True, transfers_in, transfers_out)
            net_transfers_in.append((amount, currency, source, destination))
        else:
            continue

    # Add any nft "mintTo" instruction as net transfer in (where applicable)
    if mint_to:
        _add_mint_to_as_transfers(txinfo, net_transfers_in)

    return (net_transfers_in, net_transfers_out, _transfers_unknown), fee


def _get_source_destination(currency, is_transfer_in, transfers_in, transfers_out):
    if is_transfer_in:
        for amt, cur, source, destination in transfers_in:
            if cur == currency:
                return source, destination
    else:
        for amt, cur, source, destination in transfers_out:
            if cur == currency:
                return source, destination

    raise Exception("Bad condition in _get_source_destination()")


def _log_messages(txid, data):
    log_instructions = []
    log = []

    log_messages = data["result"]["meta"]["logMessages"]
    for line in log_messages:
        match = re.search("^Program log: Instruction: (.*)", line)
        if match:
            instruction = match.group(1)
            log_instructions.append(instruction)

        match = re.search("^Program log: (.*)", line)
        if match:
            line = match.group(1)
            log.append(line)

    log_string = "\n".join(log)
    return log_instructions, log, log_string
