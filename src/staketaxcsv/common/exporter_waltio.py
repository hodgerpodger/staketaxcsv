
import csv
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


WALTIO_FIELDS = [
    "Type",
    "Date",
    "Received amount",
    "Currency or token received",
    "Sent amount",
    "Currency or token sent",
    "Fee",
    "Currency or token fee",
    "Exchange / Platform",
    "Description",
    "Label",
    "Hash",
    "ID",
]

_RE_TXHASH_64_HEX = re.compile(r"^[0-9A-Fa-f]{64}$")

_WALTIO_PLATFORM_WALLET_BASES = {
    "AKASH",
    "ALGORAND",
    "ARCHWAY",
    "COSMOS",
    "DYDX",
    "INJECTIVE",
    "NEUTRON",
    "OSMOSIS",
    "TERRA",
}

# Some IBC chains use short mintscan labels (and thus `exchange`) that don't match the
# full wallet name the user wants in Waltio.
#
# Example: Archway uses mintscan label "arch" => "arch_blockchain"
#          Neutron uses mintscan label "ntrn" => "ntrn_blockchain"
_WALTIO_PLATFORM_BASE_ALIASES = {
    "ARCH": "ARCHWAY",
    "NTRN": "NEUTRON",
}


def _waltio_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _waltio_normalize_amount(amount: Optional[Any]) -> str:
    if not amount:
        return ""
    return str(amount)


def _waltio_base_txhash(hash_val: str) -> str:
    """
    Waltio 'Hash' column should contain the real tx hash (64 hex chars).
    Internally we may suffix txids with '-0' or '-0-0' (message indexes) for uniqueness.
    Keep the suffix for ID generation, but strip it for the displayed Hash column.
    """
    if not hash_val:
        return ""

    first = hash_val.split("-", 1)[0]
    if _RE_TXHASH_64_HEX.match(first):
        return first
    return hash_val


def _waltio_token_str(token: Any) -> str:
    """Defensive conversion for token fields (keep raw value, don't rewrite symbols)."""
    if token is None:
        return ""
    return str(token).strip()


def _waltio_display_platform(platform: Any) -> str:
    """
    Normalize platform names for Waltio.

    Internally stake.tax uses values like:
      - osmosis_blockchain
      - cosmos_blockchain
      - algorand_blockchain

    User requested these to be renamed when possible:
      WALLET_AKASH, WALLET_ALGORAND, WALLET_ARCHWAY, WALLET_COSMOS, WALLET_DYDX, WALLET_INJECTIVE,
      WALLET_TERRA, WALLET_TERRA_2, WALLET_NEUTRON, WALLET_OSMOSIS, SOLANA
    """
    if platform is None:
        return ""
    s = str(platform).strip()
    if not s:
        return ""

    # already normalized
    if s.startswith("WALLET_") or s == "SOLANA":
        return s

    s_l = s.lower()
    if s_l == "solana_blockchain":
        return "SOLANA"

    if s_l.endswith("_blockchain"):
        base = s_l[: -len("_blockchain")].upper()

        # special case: Terra 2 in codebase is "luna2_blockchain"
        if base in {"LUNA2", "TERRA2"}:
            return "WALLET_TERRA_2"

        base = _WALTIO_PLATFORM_BASE_ALIASES.get(base, base)

        if base in _WALTIO_PLATFORM_WALLET_BASES:
            return f"WALLET_{base}"

    # fallback: keep as-is
    return s


class ExporterWaltio:

    def __init__(self, wallet_address: str, chain: str, export_dir: str):
        self.wallet = wallet_address
        self.chain = chain
        self.export_dir = export_dir

    def export(self, rows: List[Dict[str, Any]]) -> str:
        """
        rows = normalized transaction dict list coming from stake.tax processors.
        Expected fields per row:
            date, amount_received, token_received,
            amount_sent, token_sent,
            fee, fee_token,
            platform, memo, hash, label(optional)
        """
        output_rows: List[Dict[str, Any]] = []
        processed_lp_hashes = set()

        def _pick_fee_once(group_rows: List[Dict[str, Any]]) -> tuple[str, str]:
            for gr in group_rows:
                fee_raw = gr.get("fee")
                if fee_raw in (None, "", 0, 0.0, "0", "0.0"):
                    continue
                fee_token = gr.get("fee_token", "") or ""
                return _waltio_normalize_amount(fee_raw), fee_token
            return "", ""

        for i, r in enumerate(rows):
            amount_in = _waltio_normalize_amount(r.get("amount_received"))
            amount_out = _waltio_normalize_amount(r.get("amount_sent"))
            label_raw = (r.get("label") or "").lower()
            hash_val = r.get("hash", "")
            display_hash = _waltio_base_txhash(hash_val)

            # ---------------------------------------------------
            # Custom LP Handling: Group by Hash if multiple tokens
            # ---------------------------------------------------
            if label_raw in ["lp_withdraw", "lp_deposit"]:
                if hash_val and hash_val in processed_lp_hashes:
                    continue

                if hash_val:
                    group = [
                        row
                        for row in rows
                        if row.get("hash") == hash_val and (row.get("label") or "").lower() == label_raw
                    ]
                    processed_lp_hashes.add(hash_val)
                else:
                    group = [r]

                if label_raw == "lp_deposit":  # Add Liquidity (Sent cryptos, Received LP)
                    fee_once, fee_token_once = _pick_fee_once(group)
                    # 1. Output Withdrawal for each unique crypto sent
                    for j, gr in enumerate(group):
                        a_out = _waltio_normalize_amount(gr.get("amount_sent"))
                        if a_out:
                            output_rows.append(
                                {
                                    "Type": "Withdrawal",
                                    "Date": gr.get("date", ""),
                                    "Received amount": "",
                                    "Currency or token received": "",
                                    "Sent amount": a_out,
                                    "Currency or token sent": _waltio_token_str(gr.get("token_sent", "")),
                                    # emit fee exactly once (first output row)
                                    "Fee": fee_once if j == 0 else "",
                                    "Currency or token fee": _waltio_token_str(fee_token_once) if j == 0 else "",
                                    "Exchange / Platform": _waltio_display_platform(gr.get("platform", "")),
                                    "Description": "Add liquidity",
                                    "Label": "Add liquidity",
                                    "Hash": display_hash,
                                    "ID": (
                                        f"{self.chain}_{hash_val}_{j}_sent"
                                        if hash_val
                                        else f"{self.chain}_{i}_{j}_sent"
                                    ),
                                }
                            )

                    # 2. Sum LP tokens and output ONE Deposit
                    total_lp = 0.0
                    lp_token = ""
                    for gr in group:
                        a_in = gr.get("amount_received")
                        if a_in:
                            total_lp += float(a_in)
                            lp_token = gr.get("token_received")

                    if total_lp > 0:
                        output_rows.append(
                            {
                                "Type": "Deposit",
                                "Date": group[0].get("date", ""),
                                "Received amount": _waltio_normalize_amount(total_lp),
                                "Currency or token received": _waltio_token_str(lp_token),
                                "Sent amount": "",
                                "Currency or token sent": "",
                                "Fee": "",
                                "Currency or token fee": "",
                                "Exchange / Platform": _waltio_display_platform(group[0].get("platform", "")),
                                "Description": "Add liquidity",
                                "Label": "",
                                "Hash": display_hash,
                                "ID": (
                                    f"{self.chain}_{hash_val}_lp_received"
                                    if hash_val
                                    else f"{self.chain}_{i}_lp_received"
                                ),
                            }
                        )
                    continue

                # LP withdraw (Sent LP, Received cryptos)
                fee_once, fee_token_once = _pick_fee_once(group)
                # 1. Output Deposit for each unique crypto received
                for j, gr in enumerate(group):
                    a_in = _waltio_normalize_amount(gr.get("amount_received"))
                    if a_in:
                        output_rows.append(
                            {
                                "Type": "Deposit",
                                "Date": gr.get("date", ""),
                                "Received amount": a_in,
                                "Currency or token received": _waltio_token_str(gr.get("token_received", "")),
                                "Sent amount": "",
                                "Currency or token sent": "",
                                # Keep deposits clean: attach fee on LP-token withdrawal line below
                                "Fee": "",
                                "Currency or token fee": "",
                                "Exchange / Platform": _waltio_display_platform(gr.get("platform", "")),
                                "Description": "Liquidity withdrawal",
                                "Label": "Liquidity withdrawal",
                                "Hash": display_hash,
                                "ID": (
                                    f"{self.chain}_{hash_val}_{j}_received"
                                    if hash_val
                                    else f"{self.chain}_{i}_{j}_received"
                                ),
                            }
                        )

                # 2. Sum LP tokens and output ONE Withdrawal
                total_lp = 0.0
                lp_token = ""
                for gr in group:
                    a_out = gr.get("amount_sent")
                    if a_out:
                        total_lp += float(a_out)
                        lp_token = gr.get("token_sent")

                if total_lp > 0:
                    output_rows.append(
                        {
                            "Type": "Withdrawal",
                            "Date": group[0].get("date", ""),
                            "Received amount": "",
                            "Currency or token received": "",
                            "Sent amount": _waltio_normalize_amount(total_lp),
                            "Currency or token sent": _waltio_token_str(lp_token),
                            # emit fee exactly once for the grouped tx
                            "Fee": fee_once,
                            "Currency or token fee": _waltio_token_str(fee_token_once),
                            "Exchange / Platform": _waltio_display_platform(group[0].get("platform", "")),
                            "Description": "Liquidity withdrawal",
                            "Label": "",
                            "Hash": display_hash,
                            "ID": f"{self.chain}_{hash_val}_lp_sent" if hash_val else f"{self.chain}_{i}_lp_sent",
                        }
                    )
                continue

            # ---------------------------------------------------
            # Standard Processing for other transactions
            # ---------------------------------------------------
            if amount_in and amount_out:
                tx_type = "Trade"
            elif amount_in:
                tx_type = "Deposit"
            elif amount_out:
                tx_type = "Withdrawal"
            else:
                tx_type = ""

            label = ""
            if label_raw in ["staking"]:
                tx_type = "Deposit"
                label = "Masternode & Staking"
            elif label_raw == "airdrop":
                tx_type = "Deposit"
                label = "Airdrop"
            elif label_raw == "fee":
                tx_type = "Withdrawal"
                label = "Fee"
            elif label_raw in ["swap", "nft_trade"]:
                tx_type = "Trade"

            memo = r.get("memo", "") or ""
            memo_l = memo.lower()
            if "msgwithdrawdelegatorreward" in memo_l:
                tx_type = "Deposit"
                label = "Masternode & Staking"
            elif "fee for failed transaction" in memo_l:
                tx_type = "Withdrawal"
                label = "Fee"

            if label and memo:
                desc = f"{label} / {memo}"
            elif label:
                desc = label
            else:
                desc = memo

            hash_value = r.get("hash", "")
            uid = hash_value if hash_value else f"{self.chain}_{i}"
            display_hash_std = _waltio_base_txhash(hash_value)

            row_waltio = {
                "Type": tx_type,
                "Date": r.get("date", ""),
                "Received amount": amount_in or "",
                "Currency or token received": _waltio_token_str(r.get("token_received", "")),
                "Sent amount": amount_out or "",
                "Currency or token sent": _waltio_token_str(r.get("token_sent", "")),
                "Fee": _waltio_normalize_amount(r.get("fee")),
                "Currency or token fee": _waltio_token_str(r.get("fee_token", "")),
                "Exchange / Platform": _waltio_display_platform(r.get("platform", "")),
                "Description": desc,
                "Label": label,
                "Hash": display_hash_std,
                "ID": uid,
            }
            output_rows.append(row_waltio)

        timestamp = _waltio_timestamp()
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

        filename = f"Waltio_{self.chain}_{self.wallet}_{timestamp}.csv"
        output_path = os.path.join(self.export_dir, filename)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=WALTIO_FIELDS)
            writer.writeheader()
            writer.writerows(output_rows)

        print(f"✔ Waltio CSV exported → {output_path}")
        return output_path
