# Group Project for 'Introduction to Blockchain Technology' SoSe2020

## Supervisors
- Dr. Benjamin Leiding
- Arne Bochem

## Team 
- Akshay Katyal 
- Anant Sujatanagarjuna 
- Chris Warin 
- Mehmed Mustafa
- Rahul Agrawal 
- Steffen Tunkel

## Description
Meme economy, we got the inspiration from: `https://www.reddit.com/r/MemeEconomy/`

Demo video: https://www.youtube.com/watch?v=kS7bYrLqaDg

## API Documentation
See [html documentation](docs/_build/html/index.html)

## Running a demo test
`Format` and `Template` words are used interchangeably across the project and they mean the same thing.
Check the `memes folder` to see examples of different `templates` and `memes` created using the `templates`.

### 1. Requirements
- `Flask`==1.1.2, run `pip install Flask==1.1.2` to install it.
- `requests`==2.23.0, run `pip install requests==2.23.0` to install it.
- `Postman` HTTP Client, download it from: `https://www.getpostman.com/`

We are using `Postman` for better visualization of the input/output data. Of course, using `curl` via the command line would produce the same results, but visualization of images(memes) would not be possible.
Use `Postman` for running the demo below.

### 2. Parameters
The default parameters' values are as follows:

`MIN_TRANSACTIONS` = 1

Sets the minimum number of transactions needed inside the memory pool to start auto mining.

`AUTOMATIC_MINING` = True

If set to `True`, mining of new blocks is automatic.
If set to `False`, mining of new blocks is manual.
(described in more details below in point 6)

To change the value of the 2 parameters above check inside `flask_app.py`

`difficultyPattern` = `0000`

Our current difficulty pattern is `0000` and mining of a new block takes no more than few seconds. To change this value check inside `blockchain.py`

`NEW_NODE_INITIAL_CREDITS` = 5

The amount of initial credits each node receive after connecting to the network. To change this value check inside `validation.py`

### 3. Initialization of the Peer-to-Peer Network
All of the peers are currently running on the local network. The `core` node must run on port `5000` in order to initialize the network.

1. Run `flask_app.py` in at least 2 different Terminals with different ports as an input.
- T1: `py flask_app.py 5000`
- T2: `py flask_app.py 5001`

2. Open `Postman` and create a `POST` request by using the `connect_to_node` method to the second node and by providing the address of the `core` node in raw-JSON format in the Body of the request. The request URL in our case is: `http://127.0.0.1:5001/connect_to_node` with body input: `{"node_address":"http://127.0.0.1:5000/"}`. If the connection is successful the response will be `Connection successful` with status code 200. 

Future peers will be able to connect to the established network by sending a connection request to any of the already connected peers in the network. 

##### Events triggered after a new peer is connected:
- The new peer receives a copy of the blockchain and pending transactions of its connector (the peer accepting the connection request)
- All other peers in the network are notified about the newly connected peer

### 4. Creating transactions (NOT FINISHED COMPLETELY YET)
##### We currently support 5 different transaction types: 
- `/add_memeFormat`     - Used to add a new meme format to the network
- `/add_meme`           - Used to add a new meme to the network
- `/add_upvote`         - Used to upvote a meme inside the network
- `/sell_ownership`     - Used to sell the ownership of a meme format
- `/purchase_ownership` - Used to buy the ownership of a meme format

##### Raw-JSON body input formats of transactions:
- `/add_memeFormat`

{"imagePath" : "imagePathValue", "name" : "nameValue"}

`imagePathValue` - The path of the meme format to be uploaded.

`nameValue` - Could be any value. The name of the meme format, which will be a part of the memeFormatID assigned internally.

- `/add_meme`

{"imagePath" : "imagePathValue", "name" : "nameValue", "memeFormat" : "memeFormatID"}

`imagePathValue` - The path of the meme to be uploaded.

`nameValue` - Could be any value. The name of the meme, which will be a part of the memeID assigned internally.

`memeFormatID` - The ID of the meme format to which this meme belongs to. It is in format `A_B`. `A` is the `port number` of the node which uploaded the meme format and `B` is the `nameValue` of the meme format assigned when uploading.

- `/add_upvote`

{"imageVoteId":"memeID", "upvoteID" : "upvoteID"}

`memeID` - The ID of the meme to be up voted. It is in format `A_B`. `A` is the `port number` of the node which uploaded the meme and `B` is the `nameValue` of the meme assigned when uploading.

`upvoteID` - Could be any value. Used internally and for easier tracking of the Upvotes during the demo.

- `/sell_ownership`

{"ownershipSaleOfferID" : "ownershipSaleOfferID", "memeFormat" : "memeFormatID", "saleAmount" : "saleAmount"}

`ownershipSaleOfferID` - Could be any value. The user which wants to buy this meme format should use this ID when creating a purchase ownership transaction.

`memeFormatID` - The ID of the meme format to be sold. It is in format `A_B`. `A` is the `port number` of the node which uploaded the meme format and `B` is the `nameValue` of the meme format assigned when uploading.

`saleAmount` - The price in credits of the meme format to be sold. 

- `/purchase_ownership`

{"ownershipPurchaseID" : "ownershipPurchaseID", "ownershipSaleOfferID" : "ownershipSaleOfferID"}

`ownershipPurchaseID` - Could be any value. Used internally and for easier tracking of the purchases during the demo.

`ownershipSaleOfferID` - This is the ID value specified from the seller when creating an ownership selling transaction.

Check the video demo of the project to get an idea of example inputs for the transactions: https://www.youtube.com/watch?v=kS7bYrLqaDg
The collection of transaction requests used in the video could be imported by importing the `Meme_Economy_Blockchain.postman_collection.json` file in Postman.

##### Events triggered after a new transaction is added:
- All other peers are notified for the newly added transaction
- All other peers validate and append the new transaction to their memory pool
- All peers start mining a block if there are pending transactions

### 5. Printing all pending transactions
To check all pending transactions in the pool, it is enough to make a `GET` request by using the `/get_pending_transactions` method to any of the connected peers.
It is possible to get an empty list in case a block is mined and no other transaction is created before checking the list.

### 6. Mining a new block
Mining of a new block, on default, is an automatic process. 

Switching between auto and manual mode is possible with `AUTOMATIC_MINING` parameter.

`Auto Mining` - As soon as there are `MIN_TRANSACTIONS` amount of transactions inside the memory pool, all connected peers will start trying to mine a block. 

`Manual Mining` - Mining of a new block could also be a manual process triggered with a `GET` request by using the `/mine_block` method to any of the connected peers. Once a peer receives mining request, it will try to find a matching `nonce` value. Once a block is mined, all other peers will be notified. The manual mode is for testing purposes only and for better tracking of everything happening on the blockchain network.


##### Events triggered after a new block is mined:
- The miner checks if it has the longest valid chain (consensus mechanism)
- The miner adds the newly mined block to its local chain (if in consensus)
- All other peers are notified for the newly mined block
- All other peers validate the newly mined block and if the validation is successful they add the block to their local chains

### 7. Other useful RESTful methods
The following methods could be used on any peer.

##### 7.1 Printing the chain
Send a `GET` request by using the `/get_chain` method.

##### 7.2 Checking the validity of the chain
Send a `GET` request by using the `/check_validity` method.

##### 7.3 Checking all meme formats' and meme's information inside the network
Send a `GET` request by using the `/memeformats` method to any of the connected peers. The input format is: `{"info" : "booleanValue"}` (The input is not a must, it is optional). If the `booleanValue` is set to `True`, a more detailed information will be printed.

##### 7.4 Visualization of meme formats and memes
Send a `GET` request by using the `/visualize_meme` method. The input format is: `{"imageId" : "idValue"}`, where the `idValue` is in format `A_B`. `A` is the `port number` of the node which uploaded the meme and `B` is the `nameValue` of the meme.

Send a `GET` request by using the `/visualize_memeFormat` method. The input format is: `{"memeformatId" : "idValue"}`, where the `idValue` is in format `A_B`. `A` is the `port number` of the node which uploaded the memeFormat and `B` is the `nameValue` of the meme format.


The response in `Postman` will be an html code. To see the image, switch the response body view from `Pretty` to `Preview`

##### 7.5 Checking the credit balance of a node
Send a `GET` request by using the `/get_node_credits` method. The input format is: `{"nodeId" : "idValue"}`, where the `idValue` is the `port number` of that node.

## Final version
This is our final version for this project.
