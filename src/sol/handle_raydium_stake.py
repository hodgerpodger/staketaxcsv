import re

from common.make_tx import make_reward_tx
from sol.constants import CURRENCY_SOL, MILLION
from sol.handle_simple import handle_unknown
from sol.make_tx import make_reward_zero_tx, make_stake_tx, make_unstake_tx


def handle_raydium_stake_v5(exporter, txinfo):
    txinfo.comment = "raydium_stake_v5"
    _handle_raydium_stake(exporter, txinfo)


def handle_raydium_stake_v4(exporter, txinfo):
    txinfo.comment = "raydium_stake_v4"
    _handle_raydium_stake(exporter, txinfo)


def handle_raydium_stake(exporter, txinfo):
    txinfo.comment = "raydium_stake"
    _handle_raydium_stake(exporter, txinfo)


def _handle_raydium_stake(exporter, txinfo):
    log_instructions = txinfo.log_instructions
    transfers_in, transfers_out, _ = txinfo.transfers
    log = txinfo.log
    log_string = txinfo.log_string
    input_accounts = txinfo.input_accounts
    user_reward_token_account = input_accounts[0][6]
    pool_reward_token_account = input_accounts[0][7]

    reward_amounts = _reward_amounts(log)

    # Remove sol fee from txinfo.transfers if exists
    for i, transfer_out in enumerate(transfers_out):
        amount, currency, _, _ = transfer_out

        if amount < 0.01 and currency == CURRENCY_SOL:
            transfers_out.pop(i)
            break

    # zero reward transactions
    if len(log_instructions) == 0 and log_string == '' and len(transfers_in) == 0 and len(transfers_out) == 0:
        row = make_reward_zero_tx(txinfo)
        exporter.ingest_row(row)
        return
    elif "withdraw reward: 0" in log_string and len(transfers_in) == 0 and len(transfers_out) == 0:
        row = make_reward_zero_tx(txinfo)
        exporter.ingest_row(row)
        return
    elif "process_deposit amount: 0\n" in log_string and len(transfers_in) == 0 and len(transfers_out) == 0:
        row = make_reward_zero_tx(txinfo)
        exporter.ingest_row(row)
        return

    count = 0

    # _STAKE transaction
    if "Deposit" in log_instructions:
        for transfer_out in transfers_out:
            amount, currency, _, _ = transfer_out
            row = make_stake_tx(txinfo, amount, currency)
            exporter.ingest_row(row)
            count += 1

    if ("withdraw reward" in log_string
       or "Withdraw" in log_instructions):
        for transfer_in in transfers_in:
            amount, currency, source, destination = transfer_in

            if source == pool_reward_token_account and destination == user_reward_token_account:
                # STAKING transaction (reward)
                row = make_reward_tx(txinfo, amount, currency, z_index=10)  # Show reward tx as last row
                exporter.ingest_row(row)
            elif amount in reward_amounts:
                # STAKING transaction (reward)
                row = make_reward_tx(txinfo, amount, currency, z_index=10)  # Show reward tx as last row
                exporter.ingest_row(row)
            else:
                # _UNSTAKE transaction
                row = make_unstake_tx(txinfo, amount, currency)
                exporter.ingest_row(row)

            count += 1

    if count == 0:
        handle_unknown(exporter, txinfo)


def _reward_amounts(log):
    out = []

    for line in log:
        match = re.search(r"withdraw reward: (\w+) ", line)
        if not match:
            match = re.search(r"withdraw reward \w+: (\w+) ", line)

        if match:
            amount_string = match.group(1)
            amount = float(amount_string) / MILLION
            if amount > 0:
                out.append(amount)

    return out
