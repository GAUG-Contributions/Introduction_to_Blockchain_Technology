"""
block.py
====================================
Defines the Block structure
"""

import hashlib
import json

class Block:
    """
    Class that handles the functions and defines the structure of
    Blocks in the Blockchain
    """
    def __init__(self, index, minerID, transactions, transaction_counter, timestamp, previous_hash, proof_of_work=0):
        """
        Constructor for the Block
        """
        self.index = index
        self.minerID = minerID
        self.transactions = list(transactions)
        self.transaction_counter = transaction_counter
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.proof_of_work = proof_of_work

    def compute_hash(self):
        """
        Computes Hash of the Block
        """
        # self.__dict__ -> all variables inside the Block class
        encoded_block = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()


    def get_transactions(self):
        """
        Returns list of transactions within this Block
        """
        return self.transactions
