from cbdc.wallet import Wallet
from cbdc.uhs import UhsController


def test_processing():
    bob = Wallet()
    dave = Wallet()
    uhs = UhsController()

    assert dave.balance == 0
    assert bob.balance == 0

    minted = dave.mint_new_coins(10, 100)
    dave.receive_transfer(minted)
    assert dave.balance == 1000

    uhs.mint(minted)
    for v in dave.spendable_inputs:
        assert uhs.check_unspent(v)
