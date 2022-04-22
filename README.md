# OpenCBDC - (very) Minimal Viable Product
A simplified implementation of [OpenCBDC](https://github.com/mit-dci/opencbdc-tx) for learning and experimentation. We left out all the complex distributed application pieces
to focus on the basics of how it works.

This implementation primarily shows the 2pc architecture. You can read more about that here:
[MIT-DCI](https://dci.mit.edu/opencbdc)

## Components
- **Transaction**: Opencbdc uses a UTXO vs. an Account model, along with a compacted version for storage.
- **Wallet**: simple self-custody wallet to interact with the UHS.  Note: for simplicity we use ed25519 for signatures instead of the secp256k1 (schnorr) used in the real implementation.
- **UHS**: a very simplified version to demonstrate some of the key logic that lives across 3 (sentinel, coordinator, locking shard) separate parts of the system.

## Example
Example of sending money between 2 wallets:

```python
from cbdc.wallet import Wallet
from cbdc.uhs import UhsController

def run():
    # create wallets
    bob = Wallet()
    dave = Wallet()
    # create the UHS
    uhs = UhsController()

    assert dave.balance == 0
    assert bob.balance == 0

    # Mint money to populate the UHS. You don't normally get to do this (unfortunately)
    # Create 3 coins, each worth $5
    minted = dave.mint_new_coins(3, 5)
    uhs.mint(minted)

    # update dave's wallet
    dave.receive_transfer(minted)
    assert dave.balance == 15

    # Send $12 to bob
    tx1 = dave.transfer(12, bob.address)

    # execute the tx against the UHS
    tx2 = uhs.execute_transaction(tx1, True)
    # Bob loads the tx into his wallet
    bob.receive_transfer(tx2)

    # Bob and Dave's updated balances...
    assert dave.balance == 3
    assert bob.balance == 12


if __name__ == "__main__":
    run()
```
```text
Running the code gives you some output to show what's happening to 
transaction in the UHS. Note how there's no information about the money spent!

*** MINT ***

This is the result of the mint call

[ txid: 87b99b2f45a828e5d0715ed3ecbafd547ba406dfa9b8cad86a9f7cf0f570f8bf ]
 spending:
 creating:
  -> afc0400e53ad4fcd633d2c4ebfcfc7891605f17d49e452fa1f75000b75f2b736
  -> 1b515292c552cd257bf29ab4dd2f53bb452c752e68208e257ca3a8d799bc5744
  -> e03b15c0e545ce77da1d6afcda92b716fa6fb5bb6ad57e69ad2031258fe42b22

This is the result of the transaction between Dave andd Bob. The 
3 minted are consumed and there are now 2 new outputs: 1 for Bob and
change back to Dave


[ txid: 850fcfda81ed52bce00e42a5746dd33f8e916113205d9472174afcdfb1634516 ]
 spending:
  ↑ afc0400e53ad4fcd633d2c4ebfcfc7891605f17d49e452fa1f75000b75f2b736
  ↑ 1b515292c552cd257bf29ab4dd2f53bb452c752e68208e257ca3a8d799bc5744
  ↑ e03b15c0e545ce77da1d6afcda92b716fa6fb5bb6ad57e69ad2031258fe42b22
 creating:
  -> ac162d3a34b44bc86b0a9925a7b21b60a9f0c3a68a1ff6790306057aeb6af7f0
  -> 04350b13ed9648060d56febef9e0bc66352a29f99887dbb00e27adfc6d96c374
```


