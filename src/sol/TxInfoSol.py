import pprint

from common.TxInfo import TxInfo
from sol.constants import CURRENCY_SOL, EXCHANGE_SOLANA_BLOCKCHAIN


class TxInfoSol(TxInfo):
    """Common properties across every blockchain transaction (only)"""

    def __init__(self, txid, timestamp, fee, wallet_address):
        url = "https://solscan.io/tx/{}".format(txid)
        super().__init__(txid, timestamp, fee, CURRENCY_SOL, wallet_address, EXCHANGE_SOLANA_BLOCKCHAIN, url)

        self.instructions = None
        self.instruction_types = None
        self.program_ids = None
        self.input_accounts = None

        self.inner = None
        self.inner_parsed = None

        self.wallet_accounts = None
        self.account_to_mint = None
        self.mints = None

        self.log_instructions = None
        self.log = None
        self.log_string = None

        self.balance_changes_all = None
        self.balance_changes = None

        self.transfers = []
        self.transfers_net = []

    def print(self):
        print("txid: {}".format(self.txid))
        print("timestamp: {}".format(self.timestamp))
        print("fee: {}".format(self.fee))

        print("\ninstructions:")
        pprint.pprint(self.instructions)
        print("\ninstruction_types:")
        pprint.pprint(self.instruction_types)
        print("\nprogram_ids:")
        pprint.pprint(self.program_ids)
        print("\ninput_accounts:")
        pprint.pprint(self.input_accounts)

        print("\ninner:")
        pprint.pprint(self.inner)
        print("\ninner_parsed:")
        pprint.pprint(self.inner_parsed)

        print("\nwallet_accounts:")
        pprint.pprint(self.wallet_accounts)
        print("\naccount_to_mint:")
        pprint.pprint(self.account_to_mint)
        print("\nmints:")
        pprint.pprint(self.mints)

        print("\nlog_instructions:")
        pprint.pprint(self.log_instructions)
        print("\nlog:")
        pprint.pprint(self.log)
        print("\nlog_string:")
        pprint.pprint(self.log_string)

        print("\nbalance_changes_all:")
        pprint.pprint(self.balance_changes_all)
        print("\nbalance_changes:")
        pprint.pprint(self.balance_changes)

        print("\ntransfers_in:")
        pprint.pprint(self.transfers[0])
        print("\ntransfers_out:")
        pprint.pprint(self.transfers[1])
        print("\ntransfers_unknown:")
        pprint.pprint(self.transfers[2])

        print("\ntransfers_net_in:")
        pprint.pprint(self.transfers_net[0])
        print("\ntransfers_net_out:")
        pprint.pprint(self.transfers_net[1])
        print("\ntransfers_net_unknown")
        pprint.pprint(self.transfers_net[2])


class WalletInfo:
    def __init__(self, wallet_address):
        self.wallet_address = wallet_address
        self.staking_addrs = set()

    def add_staking_address(self, address):
        self.staking_addrs.add(address)

    def get_staking_addresses(self):
        return self.staking_addrs
