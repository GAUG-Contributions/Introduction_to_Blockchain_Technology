# Group Project for 'Introduction to Blockchain Technology' SoSe2020

## Team 
Akshay Katyal, Anant Sujatanagarjuna, Chris Warin, Mehmed Mustafa, Rahul Agrawal, Steffen Tunkel

## Description
Meme economy, we got the inspiration from: `https://www.reddit.com/r/MemeEconomy/`

The description will be elaborated more once the project is finalized.

## Running a demo test
### Requirements
- `Flask`==1.1.2, run `pip install Flask==1.1.2` to install it.
- `requests`==2.23.0, run `pip install requests==2.23.0` to install it.
- `Postman` HTTP Client, download it from: `https://www.getpostman.com/`

We are using `Postman` for better visualization of the input/output data. Of course, using `curl` via the command line would produce the same results, but visualization of images(memes) would not be possible.

### Initialization of the Peer-to-Peer Network
All of the peers are currently running on the local network. The `core` node must run on port `5000` in order to initialize the network.

1. Run `flask_app.py` in 2 different Terminals with different ports as an input.
- T1: `py flask_app.py 5000`
- T2: `py flask_app.py 5001`

2. Open `Postman` and create a `POST` request by using the `connect_to_node` method to the second node and by providing the address of the `core` node in raw-JSON format in the Body of the request. The request URL in our case is: `http://127.0.0.1:5001/connect_to_node` with body input: `{"node_address":"http://127.0.0.1:5000/"}`. If the connection is successful the response will be `Connection successful` with status code 200. 

Future peers will be able to connect to the established network by sending a connection request to any of the already connected peers in the network. 

Events triggered after a new peer is connected:
- the new peer receives a copy of the blockchain and pending transactions of its connector (the peer accepting the connection request)
- all other peers in the network are notified about the newly connected peer

### Creating a pseudo transaction
Currently we are supporting only pseudo transactions just to be able to test other functionalities in the project. In the next version we will support 3 real transactions: `UpvoteMeme`, `UploadMeme` and `UploadMemeFormat`.

To add a new transaction to the pool it is enough to make a `POST` request by using the `add_transaction` method to any of the connected peers. An example request URL: `http://127.0.0.1:5001/add_transaction` with body input: `{"sender":"Bob", "receiver":"Alice", "amount":500}`. If the transaction is added successfully the response will be "Notification: The transaction was received." with status code 201.

Events triggered after a new transaction is added:
- all other peers will be notified about the newly added transaction

Since there is a transaction in the pool, it will be now possible to mine a new block.

### Printing all pending transactions
To check all pending transactions in the pool, it is enough to make a `GET` request by using the `get_pending_transactions` method to any of the connected peers.

### Mining a new block
Currently the mining of a new block is not a 



### Printing the chain

### Checking the validity of the chain

## Version 2
