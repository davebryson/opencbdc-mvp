from __future__ import annotations

import struct
from typing import MutableSequence, Sequence

from cbdc.utils.hash import hash256


def hash_tx_input(txin: TxIn) -> bytes:
    """
    Return the hash of a TxIn
    """
    return hash256(txin.serialize())


def uhs_id_from_output(txid: bytes, idx: int, output: TxOut) -> bytes:
    """
    Generate a UHS_ID given:
     - a transaction id
     - the index of the output in tx.outputs
     - the TxOut

    Note:  The UHS_ID is a hash of a TxIn, converted to output in the wallet.  This is so
    there's a mapping between inputs -> outputs in the UHS
    """
    txin = TxIn(Outpoint(idx, txid), output)
    return hash_tx_input(txin)


class Outpoint:
    """
    Provides a reference to the transaction id and the index
    number of the output that created it...
    """

    def __init__(self, index: int, txid: bytes):
        assert len(txid) == 32, "txid should be a 32 byte hash"
        self.index: int = index
        self.txid: bytes = txid

    def serialize(self) -> bytes:
        return struct.pack("=32sQ", self.txid, self.index)

    def deserialize(raw: bytes) -> Outpoint:
        assert len(raw) == 40, "wrong number of bytes"
        txid, idx = struct.unpack("=32sQ", raw)
        return Outpoint(idx, txid)

    def __eq__(self, other: Outpoint) -> bool:
        return self.txid == other.txid and self.index == other.index


class TxOut:
    """
    Money you're spending
    """

    def __init__(self, value: float, witness: bytes):
        """
        note: using float here for value to experiment with 'change'.
        opencbdc uses atomic units (uint64)
        """
        assert len(witness) == 32, "witness should be a 32 byte hash"
        # value to spend
        self.value: float = value
        # hash(public key)
        self.witness: bytes = witness

    def serialize(self) -> bytes:
        return struct.pack("=32sd", self.witness, self.value)

    def deserialize(raw: bytes) -> TxOut:
        assert len(raw) == 40, "wrong number of bytes"
        wit, value = struct.unpack("=32sd", raw)
        return TxOut(value, wit)

    def __eq__(self, other: TxOut) -> bool:
        return self.value == other.value and self.witness == other.witness


class TxIn:
    """
    Money in your wallet
    """

    def __init__(self, outpoint: Outpoint, output: TxOut):
        self.prev_outpoint: Outpoint = outpoint
        self.prev_output_data: TxOut = output

    def serialize(self) -> bytes:
        # Should be 80 bytes
        outpoint_bytes = self.prev_outpoint.serialize()
        output_bytes = self.prev_output_data.serialize()
        return outpoint_bytes + output_bytes

    def deserialize(raw: bytes) -> TxIn:
        assert len(raw) == 80, "wrong number of bytes"
        point = Outpoint.deserialize(raw[:40])
        output = TxOut.deserialize(raw[40:])
        return TxIn(point, output)

    def __eq__(self, other: TxIn) -> bool:
        return (
            self.prev_outpoint == other.prev_outpoint
            and self.prev_output_data == other.prev_output_data
        )


class Transaction:
    """
    Full transaction
    """

    def __init__(self):
        self.inputs: MutableSequence[TxIn] = []
        self.outputs: MutableSequence[TxOut] = []
        self.witnesses: MutableSequence[bytes] = []

    def tx_id(self) -> bytes:
        data = b""
        # Prefix the length of each list
        input_bytes = struct.pack("=Q", len(self.inputs))
        output_bytes = struct.pack("=Q", len(self.outputs))
        data += input_bytes
        for i in self.inputs:
            data += i.serialize()

        data += output_bytes
        for i in self.outputs:
            data += i.serialize()

        return hash256(data)

    def serialize(self) -> bytes:
        data = b""
        input_bytes = struct.pack("=Q", len(self.inputs))
        output_bytes = struct.pack("=Q", len(self.outputs))
        wit_bytes = struct.pack("=Q", len(self.witnesses))

        data += input_bytes
        for i in self.inputs:
            data += i.serialize()

        data += output_bytes
        for i in self.outputs:
            data += i.serialize()

        data += wit_bytes
        for i in self.witnesses:
            data += i

        return data

    def deserialize(raw: bytes) -> Transaction:
        """
        TODO: the plot thickens...

        tx = Transaction()

        # serialized size = 80
        (input_len,) = struct.unpack("=Q", raw[:8])
        in_raw = raw[8 : input_len * 80 + 8]
        for i in range(input_len):
            start = i * 80
            end = start + 80
            bits = in_raw[start:end]
            tin = TxIn.deserialize(bits)
            tx.inputs.append(tin)

        # serialized size = 40
        (output_len,) = struct.unpack("=Q", raw[(input_len + 8) : (input_len + 16)])
        outraw = raw[(input_len + 16) : (input_len + 16) + (output_len * 40)]
        for i in range(output_len):
            start = i * 40
            end = start + 40
            bits = outraw[start:end]
            too = TxOut.deserialize(bits)
            tx.outputs.append(too)

        # serialized size = 96
        wit_len = struct.unpack(
            "=Q", raw[(input_len + output_len + 16) : input_len + output_len + 24]
        )
        wit_raw = raw[(input_len + output_len + 24) :]
        for i in range(wit_len):
            start = i * 96
            end = start + 96
            bits = wit_raw[start:end]
            tx.witnesses.append(bits)
        """
        pass

    def __eq__(self, other: Transaction) -> bool:
        return self.tx_id == other.tx_id


class CompactTx:
    """
    Format of the transaction once validated by the sentinel. Used to update the UHS
    """

    def __init__(self):
        self.tx_id: bytes = None
        self.spends: MutableSequence[bytes] = []
        self.creates: MutableSequence[bytes] = []

    def create(tx: Transaction):
        """
        Create a compact transaction.
        The construction of this is important to correct operation in the UHS
        """
        ctx = CompactTx()
        ctx.tx_id = tx.tx_id()
        for i in tx.inputs:
            ctx.spends.append(hash_tx_input(i))
        for idx, o in enumerate(tx.outputs):
            hashed = uhs_id_from_output(ctx.tx_id, idx, o)
            ctx.creates.append(hashed)
        return ctx

    def display(self):
        print("\n[ txid: {} ]".format(self.tx_id.hex()))
        print(" spending:")
        for i in self.spends:
            print("  {} {}".format("\u2191", i.hex()))

        print(" creating:")
        for i in self.creates:
            print("  -> {}".format(i.hex()))
