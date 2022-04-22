"""
Hashing function.  Separated to swap different hash algorithms
"""

from hashlib import sha256

HashSize = 32
ZeroHash = b"\x00" * HashSize


def hash256(*args: bytes) -> bytes:
    """
    SHA256 hash over the arguments (in the order provided).
    Returns a 32 byte hash
    """
    sha = sha256()
    for value in args:
        sha.update(value)
    return sha.digest()
