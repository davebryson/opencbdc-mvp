from cbdc.wallet import Wallet


def test_wallet():
    dave = Wallet()
    bob = Wallet()
    alice = Wallet()
    assert dave.balance == 0
    assert bob.balance == 0

    # mint money out of thin air...
    mt = dave.mint_new_coins(3, 5)
    dave.receive_transfer(mt)
    assert dave.balance == 15
    assert len(dave.spendable_inputs) == 3
    assert dave.is_my_address(dave.address)

    # Send $12 to bob
    tx1 = dave.transfer(12, bob.address)
    bob.receive_transfer(tx1)

    assert dave.balance == 3
    assert bob.balance == 12
    assert len(dave.spendable_inputs) == 1
    assert len(bob.spendable_inputs) == 1

    # Bob sends some to alice
    tx2 = bob.transfer(10.50, alice.address)
    alice.receive_transfer(tx2)
    assert bob.balance == 1.50
    assert alice.balance == 10.50
