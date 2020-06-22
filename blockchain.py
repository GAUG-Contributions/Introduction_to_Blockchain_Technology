import hashlib
import json
import datetime
import sys

import requests

from block import Block
import validation

class Blockchain:
    # difficulty level of the Proof of Work
    # shows the pattern with which each hash has to start with
    difficultyPattern = '0'

    # Constructor for Blockchain
    def __init__(self):
        # stores all blocks
        self.chain = []
        # temporaly stores all transactions which are currently not within a block
        self.transactions_to_be_confirmed = [] 

    # Creating of the Origin/First block in the chain
    def create_origin_block(self):
        # The block has empty list of transactions
        # The block has 0 as a value for index, previous_hash, proof_of_work
        origin_block = Block(0, None, [], 0, "0", 0)
        origin_block.hash = origin_block.compute_hash()
        self.chain.append(origin_block)

    # Returns the previous block of the chain
    def previous_block(self):
        return self.chain[-1]

    # Finds a value for proof_of_work which produces 
    # a hash that satisfies the difficulty pattern
    @staticmethod
    def proof_of_work(block):
        satisfying_hash = False
        block.proof_of_work = 0

        while not satisfying_hash:
            computed_hash = block.compute_hash()
            if(computed_hash.startswith(Blockchain.difficultyPattern)):
                satisfying_hash = True
            else:
                block.proof_of_work += 1

        return computed_hash

    # Checks whether the hash value of a block is valid 
    # and satisfies the difficulty pattern or not
    @classmethod
    def is_proof_valid(cls, block, block_hash):
        # If the hash of the block doesn't match with the computed hash
        if(block.compute_hash() != block_hash):
            return False

        # Check for blocks other than the origin block
        if(block.index != 0):
            # does the hash satisfy the difficulty level
            if not block_hash.startswith(Blockchain.difficultyPattern):
                return False

        return True

    # Checks whether the current chain is valid or not
    @classmethod
    def check_validity(cls, chain):
        chain_is_valid = True

        # Get origin block's hash as a starting point
        previous_hash = chain[0].hash

        for current_block in chain:
            # Skip the origin block
            if(current_block.index == 0):
                continue
            # If the previous_hash doesn't match with the previous_hash field of the current block
            if(previous_hash != current_block.previous_hash):
                chain_is_valid = False
            # Store the current block's hash
            current_block_hash = current_block.hash
            # remove the hash field of the block so the compute_hash function doesn't 
            # include this field when computing the hash while approving the validity
            delattr(current_block, "hash")
            # Approve the validity of the block
            if not(cls.is_proof_valid(current_block, current_block_hash)):
                chain_is_valid = False
            # Restore the current block's hash
            current_block.hash = current_block_hash
            # Update previous hash parameter for the next iteration
            previous_hash = current_block_hash
            # If the current block is not validated, no need to continue checking
            if not (chain_is_valid):
                break

        return chain_is_valid 

    # Appends a block to the chain after verifying it's validity
    def append_block(self, block, proof):
        if not (Blockchain.is_proof_valid(block, proof)):
            return False

        if (self.previous_block().hash != block.previous_hash):
            return False

        block.hash = proof

        success, errors = validation.apply_block(block, commit=True)
        if not success:
            return False
        
        self.chain.append(block)
        # reset the list since the transactions are confirmed now
        self.transactions_to_be_confirmed = [] #TODO Only remove
                                               #transactions that were
                                               #added to the new block

        return True

    # Adds a transaction to the list of pending transactions (mempool)
    def add_transaction(self, transaction):
        self.transactions_to_be_confirmed.append(transaction)

    # Checks whether there are pending transactions or not
    def pending_transactions(self):
        # 0 = False
        return len(self.transactions_to_be_confirmed)

    # Checks whether the blockchain contains image with imageId
    # if exists, returns image's decoded ascii value, otherwise -1
    def find_image(self, imageId):
        for Block in self.chain:
            current_block_transactions = Block.get_transactions()
            for Transaction in current_block_transactions:
                if (Transaction.get("imageId") and Transaction["imageId"] == imageId):
                    return Transaction["zEncoding64_val"]

        return -1

    # mine_block encapsulation -> to be used in app_mine_block() function
    def mine_block(self, _minerID):
        previous_block = self.previous_block()
        new_block = Block(index=previous_block.index + 1,
                          minerID=_minerID,
                          transactions=self.transactions_to_be_confirmed,
                          transaction_counter = len(self.transactions_to_be_confirmed),
                          timestamp=str(datetime.datetime.now()),
                          previous_hash=previous_block.hash,
                          proof_of_work=0)

        success, errors = validation.apply_block(new_block)

        if not success:
            erroneous_transactions = [err.trindex for err in errors]
            new_transaction_list = []
            for trindex, transaction in enumerate(new_block.transactions):
                if trindex not in erroneous_transactions:
                    new_transaction_list.append(transaction)
            new_block.transactions = new_transaction_list
            success, errors = validation.apply_block(new_block)
            if not success:
                raise Exception("Removing erroneous transactions still resulted in errors. -------\n"+str(errors))
    
        proof = self.proof_of_work(new_block)
        self.append_block(new_block, proof)

# Consensus mechanism to make sure that the nodes in 
# the network always have the longest (valid) chain
def consensus_mechanism(_chain, _connected_nodes):
    # A basic algorithm which sends /get_chain requests
    # to all other connected nodes in the network. 
    # If a longer chain is found, current node's chain is 
    # replaced in order to keep the blockchain up-to-date
    global blockchain
    current_node_chain_lenght = len(_chain)
    chain_updated = False

    for node in _connected_nodes:
        node_response = requests.get("{}get_chain".format(node))
        response_length = node_response.json()["length"] 
        response_chain = node_response.json()["chain"]
        # If the response holds longer chain and the chain is valid
        if(current_node_chain_lenght < response_length and 
            Blockchain.check_validity(response_chain)):
            # Update the length and chain
            current_node_chain_lenght = response_length
            blockchain = response_chain
            chain_updated = True

    return chain_updated

# A function which builds chain and transactions structure
# from the json data
def construct_chain_again(json_chain):
    generated_blockchain = Blockchain()
    generated_blockchain.create_origin_block()

    for block_data in json_chain:
        # Skip the Origin block
        if block_data["index"] == 0:
            continue  
        block = Block(block_data["index"],
                      block_data["minerID"],
                      block_data["transactions"],
                      block_data["transaction_counter"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["proof_of_work"])
        proof = block_data['hash']
        # If a block of the chain cannot be validated
        if not generated_blockchain.append_block(block, proof):
            raise Exception("The chain data is altered!")
    return generated_blockchain
