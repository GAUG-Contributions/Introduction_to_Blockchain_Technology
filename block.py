# Copyright 2020 Akshay Katyal, Anant Sujatanagarjuna, Chris Warin, Mehmed Mustafa, Rahul Agrawal, Steffen Tunkel

# This file is part of order66

# order66 is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# order66 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with order66.  If not, see <https://www.gnu.org/licenses/>.

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
