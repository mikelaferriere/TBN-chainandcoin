# Blockchain README

This initial implementation is a pretty simple straightforward representation of a blockchain.
It uses Proof of Work (PoW), which means that it can be mined. We may want to later use 
Proof of Stake (PoS) which should reduce transaction fees, but requires people to believe in
the product before any it produces any value.


# Install Blockchain deps
```
make pip
```

# Run blockchain api
```
make run
```


NOTE: When making POST requests, don't forget to add `-H "Content-Type: application/json"`
to the header.
