from re import T
from cbdc.transaction import (
    Outpoint,
    TxIn,
    TxOut,
    Transaction,
    hash_tx_input,
    uhs_id_from_output,
)
from cbdc.utils.keys import PUBLIC_KEY_SIZE, SIGNATURE_SIZE


def test_structure():
    fake_txid = b"\x01" * 32
    fake_witness = b"\x03" * 32
    # public_key (32) + signature (64) = 96
    fake_tx_witness = b"\x04" * (PUBLIC_KEY_SIZE + SIGNATURE_SIZE)

    # Outpoint
    op = Outpoint(1, fake_txid)
    op_back = Outpoint.deserialize(op.serialize())
    assert op == op_back

    # TxOut
    txo = TxOut(24, fake_witness)
    txo_back = TxOut.deserialize(txo.serialize())
    assert txo == txo_back

    # TxIn
    txi = TxIn(op, txo)
    txi_back = TxIn.deserialize(txi.serialize())
    assert txi == txi_back

    assert txi.prev_outpoint.index == 1
    assert txi.prev_outpoint.txid == fake_txid
    assert txi.prev_output_data.value == 24
    assert txi.prev_output_data.witness == fake_witness

    # Transaction
    ftx = Transaction()
    ftx.inputs.append(txi)
    ftx.outputs.append(txo)
    ftx.witnesses.append(fake_tx_witness)
    assert len(ftx.tx_id()) == 32

    b_ftx = ftx.serialize()
    # 24 = size of all the length prefixes
    # 40 = 1 TxOut
    # 80 = 1 TxIn
    # 96 = 1 witness
    assert len(b_ftx) == 24 + 40 + 80 + 96

    # UHS ID
    # using pieces made above
    # note index used for outpoint above (1)
    input_hash = hash_tx_input(txi)
    uhs_hash = uhs_id_from_output(fake_txid, 1, txo)
    assert input_hash == uhs_hash
