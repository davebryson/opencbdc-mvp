"""
Generate keys, sign, verify messages.

Note: opencdbc uses secp256k1 with schnorr signatures. Using ed25519 here 
for dependency simplicity.  The key and signature size are the same as schnorr.
"""
import nacl
from nacl.utils import random


from typing import Tuple

PUBLIC_KEY_SIZE = 32
SIGNATURE_SIZE = 64


def generate_keypair() -> Tuple[bytes, bytes]:
    """
    Generate an ed25519 keypair
    Returns (publickey, secretkey)
    """
    seed = random(nacl.bindings.crypto_sign_SEEDBYTES)
    return nacl.bindings.crypto_sign_seed_keypair(seed)


def sign_message(msg: bytes, secret: bytes) -> bytes:
    """
    Sign the given message.
    Returns the signature (w/o the message)
    """
    raw_signed = nacl.bindings.crypto_sign(msg, secret)
    signature = raw_signed[:SIGNATURE_SIZE]
    return signature


def verify_signature(msg: bytes, sig: bytes, pubkey: bytes) -> bool:
    """
    Verify a signature given a message, signature, and public key.
    Throws an exception if there's an invalid signature
    """
    # note: concatenating sig & msg
    expected = nacl.bindings.crypto_sign_open(sig + msg, pubkey)
    return expected == msg
