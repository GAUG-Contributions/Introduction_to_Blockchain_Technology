# Module 1 - Create a Blockmy_chain

# To be installed:
# Flask==0.12.2: pip install Flask==0.12.2
# Postman HTTP Client: https://www.getpostman.com/

# Importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify

# Part 1 - Building a Blockmy_chain

class Blockchain:

    def __init__(self):                      #private function
        self.my_chain = []
        self.create_block(proof_of_work = 1, previous_hash = '0')

    def create_block(self, proof_of_work, previous_hash):
        block = {'index': len(self.my_chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof_of_work': proof_of_work,
                 'previous_hash': previous_hash}
        self.my_chain.append(block)
        return block

    def get_previous_block(self):
        return self.my_chain[-1]

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
        encoded_block = json.dumps(block, sort_keys = True).encode()
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
            hash_operation = hashlib.sha256(str(proof_of_work**3 - previous_proof_of_work**3).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True


app = Flask(__name__)          # Creating a Web App


blockchain = Blockchain()      # Creating a Blockchain


@app.route('/mine_block', methods = ['GET'])      # Mining a new block

def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof_of_work = previous_block['proof_of_work']
    proof_of_work = blockchain.proof_of_work_of_work(previous_proof_of_work)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof_of_work, previous_hash)
    response = {'Notification': 'Awesome, Successfully,mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof_of_work': block['proof_of_work'],
                'previous_hash': block['previous_hash']}
    return jsonify(response), 200


@app.route('/get_my_chain', methods = ['GET'])       # Getting the full Blockchain

def get_my_chain():
    response = {'my_chain': blockchain.my_chain,
                'length': len(blockchain.my_chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid

@app.route('/is_valid', methods = ['GET'])

def is_valid():
    is_valid = blockchain.is_my_chain_valid(blockchain.my_chain)
    if is_valid:
        response = {'Notification': 'Blockchain is valid.'}
    else:
        response = {'Notification': 'Hey hey The Blockchain is not valid.'}
    return jsonify(response), 200

# Running the app
app.run(host = '0.0.0.0', port = 5000)
