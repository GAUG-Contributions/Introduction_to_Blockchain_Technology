import hashlib
import json

class Block:
    # Constructor for Block
    def __init__(self, index, transactions, transaction_counter, timestamp, previous_hash, proof_of_work=0):
        self.index = index
        self.transactions = transactions
        self.transaction_counter = transaction_counter
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.proof_of_work = proof_of_work

    # Computes the hash of the Block
    def compute_hash(self):
        # self.__dict__ -> all variables inside the Block class
        encoded_block = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()