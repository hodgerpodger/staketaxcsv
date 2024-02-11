import bech32
import logging
from Crypto.Hash import keccak
from typing import List, Optional


# https://eips.ethereum.org/EIPS/eip-55
# Takes a 20-byte binary address as input
def _checksum_encode(address: List[int]):
    hex_addr = bytes(address).hex()
    checksummed_buffer = ""

    k = keccak.new(digest_bits=256)
    k.update(hex_addr.encode("utf-8"))
    hashed_address = k.hexdigest()

    for nibble_index, character in enumerate(hex_addr):
        if character in "0123456789":
            checksummed_buffer += character
        elif character in "abcdef":
            # Check if the corresponding hex digit (nibble) in the hash is 8 or higher
            hashed_address_nibble = int(hashed_address[nibble_index], 16)
            if hashed_address_nibble > 7:
                checksummed_buffer += character.upper()
            else:
                checksummed_buffer += character
        else:
            raise ValueError(
                f"Unrecognized hex character {character!r} at position {nibble_index}"
            )

    return "0x" + checksummed_buffer


def from_hex_to_bech32(hrp: str, address: str) -> Optional[str]:
    """
    Convert an address from Ethereum hex to Bech32 format.

    :param hrp: Human Readable Prefix, e.g. evmos, io.
    :param address: Address in Ethereum hex format.
    """
    if not address.startswith("0x"):
        return None
    if len(address) != 42:
        return None

    try:
        address_bytes = bytes.fromhex(address[2:])
        data = bech32.convertbits(address_bytes, 8, 5)

        return bech32.bech32_encode(hrp, data)
    except Exception as e:
        logging.error("Exception converting address %s, exception=%s", address, str(e))
        return None


def from_bech32_to_hex(hrp: str, address: str) -> Optional[str]:
    """
    Convert an adress from Bech32 to Ethereum EIP55 hex format.

    :param hrp: Human Readable Prefix, e.g. evmos, io.
    :param address: Address in Bech32 format.
    """
    if not address.startswith(hrp + "1"):
        return None
    if len(address) != len(hrp) + 39:
        return None

    try:
        data = bech32.bech32_decode(address)
        decoded = bech32.convertbits(data[1], 5, 8, False)

        return _checksum_encode(decoded)
    except Exception as e:
        logging.error("Exception converting address %s, exception=%s", address, str(e))
        return None


def evmo_addrs(wallet_address):
    """ Returns ('evmos...', '0x...') given wallet_address in either format """
    return _both_formats("evmos", wallet_address)


def dym_addrs(wallet_address):
    """ Returns ('dym...', '0x...') given wallet_address in either format """
    return _both_formats("dym", wallet_address)


def _both_formats(prefix, wallet_address):
    if wallet_address.startswith("0x"):
        bech32_address = from_hex_to_bech32(prefix, wallet_address)
        return bech32_address, wallet_address
    elif wallet_address.startswith(prefix):
        hex_address = from_bech32_to_hex(prefix, wallet_address)
        return wallet_address, hex_address
    else:
        return None, None
