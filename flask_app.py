# To be installed:
# Flask==1.1.2: pip install Flask==1.1.2
# Postman HTTP Client: https://www.getpostman.com/
# requests==2.23.0: pip install requests==2.23.0

import hashlib
import json
import datetime
import sys

from flask import Flask, jsonify, request
import requests

from block import Block
from blockchain import Blockchain, consensus_mechanism as consensus, construct_chain_again as construct_chain

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

app_port = get_args(*sys.argv)
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
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["transaction_counter"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["proof_of_work"])
    proof = block_data["hash"]

    # Append the block to the chain if the block is validated
    if(blockchain.append_block(block, proof)):
        response, status_code = {"Notification": "The block was appended to the chain."}, 201
    else:
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
    transaction_data = request.get_json()
    # Store the transaction received from the network in the local transactions_to_be_confirmed list
    blockchain.add_transaction(transaction_data)
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

# POST method for pushing a new transaction to the local mempool
@app.route('/add_transaction', methods=['POST'])      
def app_add_transaction():
    # Expected JSON data format
    # {"sender":"SenderName","receiver":"ReceiverName","amount":300}
    transaction_data = request.get_json()
    transaction_keys = ["sender", "receiver", "amount"]

    # Verify if the required transaction keys are in the json
    for key in transaction_keys:
        if not transaction_data.get(key):
            return jsonify({"Error": "Missing transaction elements!"}), 400

    # Produce an index and a timestamp for the transaction
    transaction_data["index"] = len(blockchain.transactions_to_be_confirmed)
    transaction_data["timestamp"] = str(datetime.datetime.now())

    # Notify all nodes in the network for this new transaction 
    # so they can add it to their local mempool
    notify_all_nodes_new_transaction(transaction_data)

    response = {"Notification": "The transaction was received."}
    return jsonify(response), 201

# GET request for mining a block
@app.route('/mine_block', methods=['GET'])
def app_mine_block():
    # If there are no transactions to be confirmed, 
    # then there isn't a reason to mine a new block
    if not blockchain.pending_transactions():
        return jsonify({"Warning": "No pending transactions available!"}), 405

    blockchain.mine_block()
    mined_block = blockchain.previous_block()

    # Store the local lenght of the current node
    chain_length = len(blockchain.chain)
    # Check if the chain of the current node is up-to-date with the network
    consensus(blockchain.chain, connected_nodes)
    # If our lenght haven't changed, then we are up-to-date
    if chain_length == len(blockchain.chain):
        # Notify other nodes in the network for the recently mined block
        notify_all_nodes_new_block(mined_block)

    response = {"Notification": "Wohooo, you have just mined a block!",
                "Block Info": mined_block.__dict__}
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

    # Make a request to register with remote node and obtain information
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

app.run(host='0.0.0.0', port=app_port)