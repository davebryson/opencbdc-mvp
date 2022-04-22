"""
Encode and decode a wallet address. Separated to swap different approaches.

Default implementation is Bech32. The same one used by opencdbc
"""
import bech32


BECH_32_HRP = "usd"


def encode_address(public_key: bytes) -> str:
    """
    Create a bech32 encoded address from a public key.
    Return a string
    Throws an exception if the public key is not 32 bytes
    """
    assert len(public_key) == 32, "expected a public key"
    return bech32.encode(BECH_32_HRP, 1, public_key)


def decode_address(addr: str) -> bytes:
    """
    Decode an address
    Return the undelying public key as bytes
    """
    _, i = bech32.decode(BECH_32_HRP, addr)
    return bytes(i)
