"""
flask_app.py
Flask application for Meme Economy
"""


# To be installed:
# Flask==1.1.2: pip install Flask==1.1.2
# Postman HTTP Client: https://www.getpostman.com/
# requests==2.23.0: pip install requests==2.23.0

import hashlib
import json
import datetime
import sys
import base64
import threading
import time

from flask import Flask, jsonify, request
import requests

from block import Block
from blockchain import Blockchain, consensus_mechanism as consensus, construct_chain_again as construct_chain
from node_state import Nodes as map_of_nodes, MemeFormats as map_of_memeformats, Memes as map_of_memes, Upvotes as map_of_upvotes, OwnershipSaleOffers as map_of_ownershipoffers

STOP_MINING = False

AUTOMATIC_MINING = True

MINING_THREAD = None

MINING_RESULT = None

MIN_TRANSACTIONS = 1

# Creating a Flash Web App
app = Flask(__name__)

# Creating a Blockchain and creating the origin(first) Block
blockchain = Blockchain()
blockchain.create_origin_block()

# A set which holds the addresses of all connected nodes (peers)
connected_nodes = set()

# Get a port number as a parameter from the command line
# The default value is 8000 if no parameter is provided
def get_args(name='default', port="8000"):
    return int(port)

if __name__ == "__main__":
    app_port = get_args(*sys.argv)
else:
    app_port = 8000
host_address = f"http://127.0.0.1:{app_port}/"

# If this is the origin/first node with port number 5000, register it in connected_nodes
# Notice that in order for the Blockchain to work as intended, 
# the port number of the Origin Node must be 5000
if(host_address == "http://127.0.0.1:5000/"):
    connected_nodes.add(host_address)

# A function which triggers /append_block POST method of 
# other connected nodes in order to register the newly mined block
def notify_all_nodes_new_block(block):
    
    for node in connected_nodes:
        requests.post("{}append_block".format(node), 
                    data=json.dumps(block.__dict__, sort_keys=True), 
                    headers={"Content-Type": "application/json"})

# POST method for pushing a newly mined block by someone else to a node's chain
# Used internally to receive mined blocks from the network
@app.route('/append_block', methods=['POST'])
def app_append_block():
    global STOP_MINING
    global MINING_THREAD
    print("In append_block")
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["minerID"],
                  block_data["transactions"],
                  block_data["transaction_counter"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["proof_of_work"])
    proof = block_data["hash"]
    
    # Append the block to the chain if the block is validated
    if(blockchain.append_block(block, proof)):
        print("Trying to join MINING_THREAD")
        STOP_MINING = True
        if MINING_THREAD is not None:
            MINING_THREAD.join()
        STOP_MINING = False
        print("Should enable mining again")
        response, status_code = {"Notification": "The block was appended to the chain."}, 201
    else:
        print("Error, block was invalid")
        response, status_code = {"Error": "The block was invalid and discarded!"}, 400

    return jsonify(response), status_code

# A function which triggers /append_transaction POST method of 
# other connected nodes in order to register the new transactions
def notify_all_nodes_new_transaction(transaction):
    for node in connected_nodes:
        requests.post("{}append_transaction".format(node), 
                    data=json.dumps(transaction, sort_keys=True), 
                    headers={"Content-Type": "application/json"})

# POST method for pushing a new transaction by someone else to a node's mempool
# Used internally to receive new transactions from the network
@app.route('/append_transaction', methods=['POST'])
def app_append_transaction():
    global MINING_THREAD
    transaction_data = request.get_json()
    # Store the transaction received from the network in the local transactions_to_be_confirmed list
    blockchain.add_transaction(transaction_data)

    new_block = blockchain.create_naked_block(app_port)#Remove transactions that are not valid
    
    if len(new_block.transactions) >= MIN_TRANSACTIONS and AUTOMATIC_MINING:
        MINING_THREAD = threading.Thread(target = mine_block_new_thread, args=(new_block,))
        MINING_THREAD.start()
        print("Minimum number of transactions `{}`  met. Starting to Mine new Block.".format(MIN_TRANSACTIONS))
    return "Created", 201

# A function which triggers /update_nodes_list POST method of 
# other connected nodes in order to register the most recently connected node
def notify_all_nodes_new_node(host_address, node_address):
    for node in connected_nodes:
        # Avoid unnecessary method calls:
        # skip the most recently connected node (node_address) 
        # skip the node (host_address) which triggered notify_all_nodes_new_node method
        if(node == node_address["node_address"] or node == host_address):
            continue
        requests.post("{}update_nodes_list".format(node), 
                    data=json.dumps(node_address, sort_keys=True), 
                    headers={"Content-Type": "application/json"})

# POST method for pushing a new peer by someone else to a node's mempool
# Used internally to connect nodes from the network
@app.route('/update_nodes_list', methods=['POST'])
def app_update_nodes_list():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # If the node is not already registered in the network
    if not node_address in connected_nodes:
        # Add the new node to the connected_nodes
        connected_nodes.add(node_address)
    return "Created", 201

# GET request for checking if the node's copy of the Blockchain is valid
@app.route('/check_validity', methods = ['GET'])
def app_check_validity():
    if(Blockchain.check_validity(blockchain.chain)):
        response, status_code = {"Chain Validation": "The current state of the Blockchain is valid!"}, 200
    else:
        response, status_code = {"Chain Validation": "OPS! The current state of the Blockchain is not valid!"}, 200

    return jsonify(response), status_code

# GET request for getting the node's copy of the Blockchain
@app.route('/get_chain', methods = ['GET'])       
def app_get_chain():
    # Make blocks inside the chain json serializable
    blocks_data = []
    for block in blockchain.chain:
        blocks_data.append(block.__dict__)

    # Create a response
    response = {"length": len(blocks_data), 
                "chain": blocks_data,
                "peers": list(connected_nodes),
                "pending transactions": blockchain.transactions_to_be_confirmed}
    return jsonify(response), 200

# GET request for pending transactions
@app.route('/get_pending_transactions', methods = ['GET'])
def app_get_pending_transactions():
    response = {"pending_transactions": blockchain.transactions_to_be_confirmed}
    return jsonify(response), 200

def image_base64encoding(imagePath):
    with open(imagePath, "rb") as media_file:
        encoded_image = base64.b64encode(media_file.read())

    return encoded_image

# NOTE: The image id's are currently not unique and collisions are possible



@app.route("/add_meme", methods=["POST"])
def app_add_meme_transaction():
    """
    POST method for pushing a new meme transaction to the local mempool
    Expected JSON data formats
    {"imagePath":"block.jpg", "name": "nameValue", "memeFormat" : "memeFormatID"}
    """
    transaction_data = request.get_json()
    
    
    if not transaction_data.get("imagePath"):
        return jsonify({"Error": "Missing imagePath element!"}), 400
    if not transaction_data.get("name"):
        return jsonify({"Error": "Missing name element!"}), 400
    encodedImage = image_base64encoding(transaction_data["imagePath"])

    # Append the base64 encoding of the Meme or MemeFormat
    transaction_data["zEncoding64_val"] = encodedImage.decode('ascii')
    # Append the base64 encoding length
    transaction_data["zEncoding64_len"] = len(encodedImage)
    
    host_port = request.host.split(":")[1]
    # Append image ID -> Format: HostPort_MemeName
    transaction_data["imageId"] = "{}_{}".format(host_port, transaction_data["name"])

    host_port = request.host.split(":")[1]
    # Append image ID -> Format: HostPort_MemeName
    transaction_data["imageId"] = "{}_{}".format(host_port, transaction_data["name"])


    
    # Get IP and Port of the Node calling this method
    transaction_data["senderHost"] = request.host
    transaction_data["nodeID"] = app_port # Temporary NodeID for V3
    # Produce an index and a timestamp for the transaction
    transaction_data["tx_index"] = len(blockchain.transactions_to_be_confirmed)
    transaction_data["timestamp"] = str(datetime.datetime.now())
    
    # Notify all nodes in the network for this new transaction 
    # so they can add it to their local mempool

    transaction_data["type"] = "Meme"
    notify_all_nodes_new_transaction(transaction_data)

    response = {"Notification": "The transaction was received."}
    return jsonify(response), 201


@app.route("/add_memeFormat", methods=["POST"])
def app_add_memeFormat_transaction():
    """
    POST method for pushing a new memeFormat transaction to the local mempool
    Expected JSON data formats
    {"imagePath":"block.jpg", "name": "nameValue"}
    """
    transaction_data = request.get_json()
    
    if not transaction_data.get("imagePath"):
        return jsonify({"Error": "Missing imagePath element!"}), 400
    if not transaction_data.get("name"):
        return jsonify({"Error": "Missing name element!"}), 400
    encodedImage = image_base64encoding(transaction_data["imagePath"])

    # Append the base64 encoding of the Meme or MemeFormat
    transaction_data["zEncoding64_val"] = encodedImage.decode('ascii')
    # Append the base64 encoding length
    transaction_data["zEncoding64_len"] = len(encodedImage)
    
    host_port = request.host.split(":")[1]
    # Append image ID -> Format: HostPort_MemeName
    transaction_data["imageId"] = "{}_{}".format(host_port, transaction_data["name"])

    host_port = request.host.split(":")[1]
    # Append image ID -> Format: HostPort_MemeName
    transaction_data["imageId"] = "{}_{}".format(host_port, transaction_data["name"])


    
    # Get IP and Port of the Node calling this method
    transaction_data["senderHost"] = request.host
    transaction_data["nodeID"] = app_port # Temporary NodeID for V3
    # Produce an index and a timestamp for the transaction
    transaction_data["tx_index"] = len(blockchain.transactions_to_be_confirmed)
    transaction_data["timestamp"] = str(datetime.datetime.now())

    # Notify all nodes in the network for this new transaction 
    # so they can add it to their local mempool

    transaction_data["type"] = "MemeFormat"
    notify_all_nodes_new_transaction(transaction_data)

    response = {"Notification": "The transaction was received."}
    return jsonify(response), 201


@app.route("/add_upvote", methods=["POST"])
def app_add_upvote_transaction():
    """
    POST method for pushing a new upvote transaction to the local mempool
    Expected JSON data formats
    {"imageVoteId":"memeID", "upvoteID" : "upvoteID"}
    """
    transaction_data = request.get_json()

    if not transaction_data.get("imageVoteId"):
        return jsonify({"Error": "Missing imageId element!"}), 400

    # Get IP and Port of the Node calling this method
    transaction_data["senderHost"] = request.host
    transaction_data["nodeID"] = app_port # Temporary NodeID for V3
    # Produce an index and a timestamp for the transaction
    transaction_data["tx_index"] = len(blockchain.transactions_to_be_confirmed)
    transaction_data["timestamp"] = str(datetime.datetime.now())

    # Notify all nodes in the network for this new transaction 
    # so they can add it to their local mempool

    transaction_data["type"] = "Upvote"
    notify_all_nodes_new_transaction(transaction_data)

    response = {"Notification": "The transaction was received."}
    return jsonify(response), 201


@app.route("/sell_ownership", methods=["POST"])
def app_sell_ownership_transaction():
    """
    POST method for pushing a new ownership sale offer transaction to the local mempool
    Expected JSON data formats
    {"ownershipSaleOfferID": "ownershipSaleOfferID", "memeFormat":"memeFormatID", "saleAmount" : "saleAmount"}
    """
    transaction_data = request.get_json()

    
    if not transaction_data.get("ownershipSaleOfferID"):
        return jsonify({"Error" : "Missing ownershipSaleOfferID element"}), 400
    
    if not transaction_data.get("memeFormat"):
        return jsonify({"Error" : "Missing memeFormat element"}), 400

    if not transaction_data.get("saleAmount"):
        return jsonify({"Error" : "Missing saleAmount element"}), 400
    # Get IP and Port of the Node calling this method
    transaction_data["senderHost"] = request.host
    transaction_data["nodeID"] = app_port # Temporary NodeID for V3
    # Produce an index and a timestamp for the transaction
    transaction_data["tx_index"] = len(blockchain.transactions_to_be_confirmed)
    transaction_data["timestamp"] = str(datetime.datetime.now())

    
    transaction_data["type"] = "OwnershipSaleOffer"

    notify_all_nodes_new_transaction(transaction_data)
    response = {"Notification": "The transaction was received."}
    return jsonify(response), 201

@app.route("/purchase_ownership", methods=["POST"])
def app_purchase_ownership_transaction():
    """
    POST method for pushing a new ownership purchase transaction to the local mempool
    Expected JSON data formats
    {
    "ownershipPurchaseID":"ownershipPurchaseID",
    "ownershipSaleOfferID":"ownershipSaleOfferID"}
    """
    transaction_data = request.get_json()
    
    if not transaction_data.get("ownershipPurchaseID"):
        return jsonify({"Error" : "Missing ownershipPurchaseID element"}), 400

    
    if not transaction_data.get("ownershipSaleOfferID"):
        return jsonify({"Error" : "Missing ownershipSaleOfferID element"}), 400
    
    # Get IP and Port of the Node calling this method
    transaction_data["senderHost"] = request.host
    transaction_data["nodeID"] = app_port # Temporary NodeID for V3
    # Produce an index and a timestamp for the transaction
    transaction_data["tx_index"] = len(blockchain.transactions_to_be_confirmed)
    transaction_data["timestamp"] = str(datetime.datetime.now())

    
    transaction_data["type"] = "OwnershipPurchase"

    notify_all_nodes_new_transaction(transaction_data)
    response = {"Notification": "The transaction was received."}
    return jsonify(response), 201


# GET method for visualizing image by it's name
@app.route('/get_meme', methods=['GET'])
def app_get_meme():
    # Expected JSON data format
    # {"imageId":"idValue"}
    image_data = request.get_json()

    if not image_data.get("imageId"):
        return jsonify({"Error": "Missing imageName element!"}), 400

    image_ascii = blockchain.find_image(image_data["imageId"])

    if(image_ascii == -1):
        return jsonify({"Error": "Image was not found!"}), 400

    html_image = "<html><img src='data:image/jpg; base64, " + image_ascii + "'></html>"

    return html_image, 201

# GET method for getting (wallet) credit amount for a node
@app.route('/get_node_credits', methods=['GET'])
def app_get_node_credits():
    # Excepted JSON data format
    # {"nodeId" : "idValue"}
    node_data = request.get_json()
    if not node_data.get("nodeId"):
        return jsonify({"Error" : "Missing nodeId element"}), 400
    node_id = node_data.get("nodeId")
    if node_id not in map_of_nodes:
        return jsonify({"Error" : "Node `{}` not found".format(node_id)})

    response = str(vars(map_of_nodes[node_id].wallet))
    
    return jsonify(response), 201


@app.route("/node_state", methods=["GET"])
def app_get_node_state():
    """
    Get all the objects currently tracked by node_state
    """
    Nodes = {}
    MemeFormats = {}
    Memes = {}
    Upvotes = {}
    OwnershipSaleOffers = {}

    ns = {"Nodes" : map_of_nodes,
          "MemeFormats" : map_of_memeformats,
          "Memes" : map_of_memes,
          "Upvotes" : map_of_upvotes,
          "OwnershipSaleOffers" : map_of_ownershipoffers}
    response = ns

    return jsonify(response), 201


# GET request for mining a block
@app.route('/mine_block', methods=['GET'])
def app_mine_block():
    # If there are no transactions to be confirmed, 
    # then there isn't a reason to mine a new block
    if not blockchain.pending_transactions():
        return jsonify({"Warning": "No pending transactions available!"}), 405
    new_block = blockchain.create_naked_block(app_port)#Remove transactions that are not valid

    satisfying_hash = False
    new_block.proof_of_work = 0
    print("In Manual Mining Mode")
    while (not satisfying_hash) and (not STOP_MINING):
        computed_hash = new_block.compute_hash()
        if(computed_hash.startswith(Blockchain.difficultyPattern)):
            satisfying_hash = True
            new_block.hash = computed_hash
        else:
            new_block.proof_of_work += 1
    if STOP_MINING:
        MINING_RESULT = False
        response = "Stopped Mining Because another valid block was recieved"
        return jsonify(response), 200
    
    print("Congo! We mined something")
    notify_all_nodes_new_block(new_block)
    
    response = vars(new_block)
    return jsonify(response), 200

# POST method for connecting a new node to the network
# Used internally to receive connections from nodes 
# which are not part of the network yet
@app.route('/connect_node', methods=['POST'])
def app_connect_new_nodes():
    json_address = request.get_json()
    if not json_address["node_address"]:
        return jsonify({"Error": "Missing node_address element!"}), 400

    # If the node is not already registered in the network
    if not json_address["node_address"] in connected_nodes:
        # Add the new node to the connected_nodes list
        connected_nodes.add(json_address["node_address"])
        # Notify all nodes in the network for this new node
        notify_all_nodes_new_node(request.host_url, json_address)

    # Returns the most recent chain and transactions version
    # so the most recently connected node can synchronize
    return app_get_chain()


def connect_to_node(node_address):
    """
    Connect to the default node
    """
     # Make a request to register with remote node and obtain information
    response = requests.post("{}connect_node".format(node_address),
                             data=json.dumps({"node_address": "http://127.0.0.1:{}/".format(app_port)}), 
                             headers={"Content-Type": "application/json"})

    # If we are successfully connected to the network,
    # get the dump of the up-to-date chain and transactions
    # and construct the local copy of them. This response 
    # is a result of the return app_get_chain() in /connect_code
    if response.status_code == 200:
        global blockchain
        global connected_nodes
        # update chain, pending transactions and the connected_nodes
        blockchain = construct_chain(response.json()['chain'])
        blockchain.transactions_to_be_confirmed = response.json()['pending transactions']
        connected_nodes.update(response.json()['peers'])
        return "Connection successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code

# A function which triggers /connect_node POST method to 
# connect to the network and get up-to-data chain and transactions information
@app.route('/connect_to_node', methods=['POST'])
def app_connect_to_node():
    #Internally calls the `register_node` endpoint to
    #register current node with the node specified in the
    #request, and sync the blockchain as well as peer data.

    node_address = request.get_json()["node_address"]
    if not node_address:
        return jsonify({"Error": "Missing node_address element!"}), 400

    response = requests.post("{}connect_node".format(node_address),
                             data=json.dumps({"node_address": request.host_url}), 
                             headers={"Content-Type": "application/json"})

    # If we are successfully connected to the network,
    # get the dump of the up-to-date chain and transactions
    # and construct the local copy of them. This response 
    # is a result of the return app_get_chain() in /connect_code
    if response.status_code == 200:
        global blockchain
        global connected_nodes
        # update chain, pending transactions and the connected_nodes
        blockchain = construct_chain(response.json()['chain'])
        blockchain.transactions_to_be_confirmed = response.json()['pending transactions']
        connected_nodes.update(response.json()['peers'])
        return "Connection successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code

def mine_block_new_thread(block):
    """
    Function used inside the thread used to start mining in a new
    thread
    """
    global MINING_RESULT
    satisfying_hash = False
    block.proof_of_work = 0
    print("In Mining Thread.")
    while (not satisfying_hash) and (not STOP_MINING):
        computed_hash = block.compute_hash()
        if(computed_hash.startswith(Blockchain.difficultyPattern)):
            satisfying_hash = True
            block.hash = computed_hash
        else:
            block.proof_of_work += 1
    if STOP_MINING:
        MINING_RESULT = False
        return
    MINING_RESULT = block
    print("Congo! We mined something")

    def temporary_thread_to_notify_new_block(block):
        notify_all_nodes_new_block(block)
        
    if not consensus(blockchain.chain, connected_nodes):
        tempoth  = threading.Thread(target=temporary_thread_to_notify_new_block, args=(block,))
        tempoth.start()


# This is not something we would like to have,
# it makes the network in some sense centralized.
# If the node running on port 5000 ever disconnects,
# no other nodes can connect to the network anymore.  

#if app_port != 5000:
#    connect_to_node("http://127.0.0.1:5000/")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=app_port)

