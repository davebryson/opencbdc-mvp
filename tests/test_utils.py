import pytest

from nacl.exceptions import BadSignatureError

from cbdc.utils.hash import hash256
from cbdc.utils.address import encode_address, decode_address
from cbdc.utils.keys import generate_keypair, sign_message, verify_signature


def test_keys():
    msg = hash256(b"dave")
    p, s = generate_keypair()
    sig = sign_message(msg, s)

    assert verify_signature(msg, sig, p)

    forged = sig[:-1] + bytes([int(sig[-1]) ^ 1])
    with pytest.raises(BadSignatureError):
        verify_signature(msg, forged, p)


def test_addresses():
    p, _ = generate_keypair()
    addr = encode_address(p)

    assert addr[:3] == "usd"
    assert p == decode_address(addr)
    with pytest.raises(AssertionError):
        encode_address(b"bob")
