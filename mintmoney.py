"""
Example: mint money to a wallet
"""

from cbdc.wallet import Wallet
from cbdc.uhs import UhsController


def run():
    # create some wallets
    dave = Wallet()

    # create the UHS
    uhs = UhsController()

    # mint some money 5 'coins' at $2 a piece
    mint_tx = dave.mint_new_coins(5, 2)
    # update the uhs
    uhs.mint(mint_tx)

    # update my wallet
    dave.receive_transfer(mint_tx)

    print(f"   wallet balance: ${dave.balance}")

    # check the UHS for valid money
    for v in dave.spendable_inputs:
        print(f"   is spendable?: {uhs.check_unspent(v)}")


if __name__ == "__main__":
    run()
