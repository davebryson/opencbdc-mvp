from typing import MutableSet

from cbdc.utils.hash import hash256
from cbdc.utils.keys import verify_signature
from cbdc.transaction import CompactTx, Transaction, TxIn, hash_tx_input


class UhsController:
    """
    A simplified version of the UHS.  Three keys components of the architecture:
    - sentinel (validation)
    - coordinator (batches incoming txs, coordinates with the shard layer)
    - locking_shard (handle 2pc: lock inputs, add new outputs and storage)
    These are condensed down (removes all the hard distributed computing)
    to the minimal logic for experimentation and demo purposes.
    Storage is a simple set of the hashed spendable outputs (via CompactTx)
    """

    def __init__(self):
        self.uhs: MutableSet[bytes] = set()

    def execute_transaction(self, tx: Transaction, maybe_display=False) -> Transaction:
        # happens on the sentinel
        self.validate(tx)
        self.process(tx, maybe_display)
        return tx

    def validate(self, tx: Transaction) -> bool:
        check_structure(tx)
        check_inputs_outputs(tx)
        check_witness_and_signature(tx)
        return True

    def mint(self, tx: Transaction):
        """
        Special method just for demo. Bypasses validation to bootstrap the bank
        """
        print("\n *** MINT ***")
        self.process(tx, True)
        return tx

    def process(self, tx: Transaction, maybe_display: bool) -> bool:
        # note: this is actually done on the sentinel
        cmptx = CompactTx.create(tx)
        if maybe_display:
            cmptx.display()

        #
        # Simplified version of what happens in each shard.
        # A shard uses an additional set (not used here) to 'lock' on the inputs
        # until the transaction has completed.  The locks are cleared after the 'creates' below
        #

        # remove what we're spending from the uhs
        for s in cmptx.spends:
            if s in self.uhs:
                self.uhs.remove(s)

        # add all the new ouputs created as the result of the transaction
        for c in cmptx.creates:
            self.uhs.add(c)

    def check_unspent(self, spendable: TxIn) -> bool:
        """
        Is the given 'TxIn' spendable (in the UHS)?
        """
        hashed = hash_tx_input(spendable)
        return hashed in self.uhs


### Validation Helpers ###


def check_structure(tx: Transaction):
    assert len(tx.inputs) > 0, "validation: missing inputs"
    assert len(tx.outputs) > 0, "validation: missing outputs"
    assert len(tx.inputs) == len(
        tx.witnesses
    ), "validation: number of witnesses don't match the number of inputs"


def check_inputs_outputs(tx: Transaction):
    in_value = 0
    out_value = 0
    for i in tx.inputs:
        in_value += i.prev_output_data.value
    for o in tx.outputs:
        out_value += o.value
    assert in_value == out_value, "validation: input and output values don't match"


def check_witness_and_signature(tx: Transaction, idx: int):
    txid = tx.tx_id()
    for idx, full_committment in enumerate(tx.witnesses):
        # get the pubkey (first 32 bytes)
        pk = full_committment[:32]
        # get the signature (remaining 64 bytes)
        sig = full_committment[32:]

        # recreate and compare the commitments
        wit_hash = hash256(pk)
        assert (
            wit_hash == tx.inputs[idx].prev_output_data.witness
        ), "witness committments don't match!"

        # check the signature
        assert verify_signature(txid, sig, pk), "bad signature!"
