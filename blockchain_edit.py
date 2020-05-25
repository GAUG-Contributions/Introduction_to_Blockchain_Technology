# Added two new functions, to add a transaction to blockchain and replace chain that will help to replace the chain with longest chain, but that will not work as chain is not decentralize, I am still working on that.

# To be installed:
# Flask==0.12.2: pip install Flask==0.12.2
# Postman HTTP Client: https://www.getpostman.com/
# requests==2.18.4: pip install requests==2.18.4

# Importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


# Part 1 - Building a Blockchain

class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof_of_work = 1, previous_hash = '0')
        self.nodes = set()

    def create_block(self, proof_of_work, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof_of_work': proof_of_work,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work_of_work(self, previous_proof_of_work):
        new_proof_of_work = 1
        check_proof_of_work = False
        while check_proof_of_work is False:
            hash_operation = hashlib.sha256(str(new_proof_of_work**3 - previous_proof_of_work**3).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof_of_work = True
            else:
                new_proof_of_work += 1
        return new_proof_of_work

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_my_chain_valid(self, my_chain):
        previous_block = my_chain[0]
        block_index = 1
        while block_index < len(my_chain):
            block = my_chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof_of_work = previous_block['proof_of_work']
            proof_of_work = block['proof_of_work']
            hash_operation = hashlib.sha256(str(proof_of_work ** 3 - previous_proof_of_work ** 3).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transaction(self, sender, receiver, amt):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amt})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False


# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')

# Creating a Blockchain
blockchain = Blockchain()


# Mining a new block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof_of_work = previous_block['proof_of_work']
    proof_of_work = blockchain.proof_of_work_of_work(previous_proof_of_work)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address, receiver='xyz_person', amount=1)
    block = blockchain.create_block(proof_of_work, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

@app.route('/get_my_chain', methods = ['GET'])       # Getting the full Blockchain

def get_my_chain():
    response = {'my_chain': blockchain.my_chain,
                'length': len(blockchain.my_chain)}
    return jsonify(response), 200


def is_valid():
    is_valid = blockchain.is_my_chain_valid(blockchain.my_chain)
    if is_valid:
        response = {'Notification': 'Blockchain is valid.'}
    else:
        response = {'Notification': 'Hey hey The Blockchain is not valid.'}
    return jsonify(response), 200


@app.route('/add_transaction', methods=['POST'])      # Adding a new transaction to blockchain
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201

# Running the app
app.run(host='0.0.0.0', port=5000)
