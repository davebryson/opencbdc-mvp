from typing import NoReturn, Sequence, MutableSequence, Tuple, Union, MutableMapping

from cbdc.utils.hash import hash256
from cbdc.utils.keys import generate_keypair, sign_message
from cbdc.utils.address import encode_address, decode_address
from cbdc.transaction import Transaction, TxOut, TxIn, Outpoint


class Wallet:
    """
    In-memory wallet
    """

    def __init__(self):
        # wallet balance
        self.balance: int = 0
        # list of my public keys (NOT USED)
        self.pubkeys: Sequence[bytes] = []
        # inputs I can spend
        self.spendable_inputs: MutableSequence[TxIn] = []
        # map of keypairs pubkey => secret key
        self.pubkey_to_secretkey: MutableMapping[bytes, bytes] = {}
        # map of witness commitments: pubkey => hash(pubkey)
        self.witness_committments: MutableMapping[bytes, bytes] = {}

    def mint_new_coins(self, num_output: int, value: int) -> Transaction:
        """
        Mint 'num_output' coins, each with a 'value'
        Return the transaction
        """
        tx1 = Transaction()
        for _i in range(num_output):
            payee = self._generate_key()
            committment = self._get_witness_committment(payee)
            tx1.outputs.append(TxOut(value, committment))
            # add to wallet state
            self.witness_committments[payee] = committment
        return tx1

    @property
    def address(self) -> str:
        """
        Returns an address for this wallet.  Note: a wallet can have many addresses
        """
        pubkey = self._generate_key()
        return encode_address(pubkey)

    def is_my_address(self, address: str) -> bool:
        """
        Is 'address' one of mine?
        """
        decoded_pk = decode_address(address)
        return decoded_pk in self.pubkey_to_secretkey

    def receive_transfer(self, tx: Transaction) -> NoReturn:
        """
        Load the wallet from a transaction to update my balance and money
        """
        self._update_balance(tx)

    ### helpers ###

    def transfer(self, amount: int, receiver: str):
        """
        Create a transaction to transfer 'amount' to 'receiver'
        """
        tx = self._transfer(amount, receiver)

        # TODO: Call UHS for validation...then update

        self._update_balance(tx)
        return tx

    ### helpers ###

    def _transfer(self, amount: int, receiver: str) -> Transaction:
        payee = decode_address(receiver)

        total, tx = self._accumulate_inputs(amount)
        comm = self._get_witness_committment(payee)

        tx.outputs.append(TxOut(amount, comm))

        if total > amount:
            # change due, send to me by creating an TxOut
            change = total - amount
            change_address = self._generate_key()
            committment = self.witness_committments[change_address]
            tx.outputs.append(TxOut(change, committment))

        txid = tx.tx_id()
        for ip in tx.inputs:
            comm = ip.prev_output_data.witness
            # this is an extra check
            pubkey = self._get_pubkey_for_witness_committment(comm)
            if pubkey:
                # If I own the public key for the committment in the input, I can spend it
                sec = self.pubkey_to_secretkey[pubkey]
                sig = sign_message(txid, sec)
                wit = pubkey + sig
                tx.witnesses.append(wit)

        return tx

    def _generate_key(self) -> bytes:
        """
        Generates keys and adds to wallet state
        Your wallet will have many of these...
        Returns the public key
        """
        p, s = generate_keypair()
        # add to wallet state
        self.pubkeys.append(p)
        self.pubkey_to_secretkey[p] = s
        # seed committments
        self.witness_committments[p] = self._get_witness_committment(p)
        return p

    def _get_witness_committment(self, pubkey: bytes) -> bytes:
        """
        Return a hash of the public key.  Note: opencbdc prefixes the pubkey with 0x0
        as an identifier
        """
        return hash256(pubkey)

    def _has_witness_committment(self, committment) -> bool:
        """
        Check if this is a committment from this wallet.
        A committment is a hash of a public key.
        """
        for value in self.witness_committments.values():
            if value == committment:
                return True
        return False

    def _get_pubkey_for_witness_committment(
        self, witness_committment
    ) -> Union[bytes, None]:
        """
        Get the publickey associated with a witness committment
        """
        for pubkey, committment in self.witness_committments.items():
            if committment == witness_committment:
                return pubkey
        return None

    def _from_outputs(self, tx: Transaction) -> Sequence[TxIn]:
        """
        Convert the outputs in the given transaction to the wallet inputs (what I can spend)
        """
        total = len(tx.outputs)
        if total == 0:
            return []
        results = []
        txid = tx.tx_id()
        for i in range(total):
            txo = tx.outputs[i]
            if self._has_witness_committment(txo.witness):
                # it's for me...add to my wallet
                tin = TxIn(Outpoint(i, txid), txo)
                results.append(tin)
        return results

    def _update_balance(self, tx: Transaction):
        """
        Update the balance of the wallet IFF, the TxOut is for me
        """
        inputs = self._from_outputs(tx)
        for v in inputs:
            if self._has_witness_committment(v.prev_output_data.witness):
                self.balance += v.prev_output_data.value
                self.spendable_inputs.append(v)

    def _accumulate_inputs(self, amount: int) -> Tuple[int, Transaction]:
        """
        Gather all my inputs that I can spend and create a transaction
        Returns (the total amount of inputs, Transaction)
        """
        assert len(self.spendable_inputs) > 0, "you're broke!"

        tx = Transaction()
        total = 0
        idx = 0

        # consume spendables (money in my wallet) till I reach 'amount'
        for inp in self.spendable_inputs:
            total += inp.prev_output_data.value
            tx.inputs.append(inp)
            idx += 1
            if total >= amount:
                break

        assert total >= amount, "insufficient funds!"

        # reduce my balance
        for i in range(idx):
            self.balance -= self.spendable_inputs[i].prev_output_data.value

        # delete the spendables I used for the tx
        del self.spendable_inputs[:idx]

        return (total, tx)
