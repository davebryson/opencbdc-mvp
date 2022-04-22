# OpenCBDC - (very) Minimal Viable Product
A simplified implementation of [OpenCBDC](https://github.com/mit-dci/opencbdc-tx) for learning and experimentation. We left out all the complex distributed application pieces
to focus on the basics of how it works.

This implementation focuses on the 2pc architecture.

## Components
- Transaction: Opencbdc uses a UTXO vs. Account model along with a compact version for storage.
- Wallet: simple self-custody wallet to interact with the UHS.  Note: for simplicity we use ed25519 for signatures instead of secp256k1 (schnorr)
- UHS: a very simplified version the demonstrate key logic that lives across 3 separate 
part of the system.

## Example
Example of sending money between 2 wallets:

```python
# Create a wallet for Dave and Bob
dave = Wallet()
bob = Wallet()

# Mint money to populate the UHS. You wouldn't normally get to do this...
# Create 3 coins, each worth $5
mt = dave.mint_new_coins(3, 5)
dave.receive_transfer(mt)

# Dave has $15
assert dave.balance == 15

# Send $12 to bob
tx1 = dave.transfer(12, bob.address)
# Bob loads the tx into his wallet
bob.receive_transfer(tx1)

# Bob and Dave's updated balances...
assert dave.balance == 3
assert bob.balance == 12
```


