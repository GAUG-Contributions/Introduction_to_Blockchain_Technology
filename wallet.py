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
wallet.py
==================
Module that handles operations relating to a node's wallet
"""

from decimal import Decimal
class NotEnoughCreditsException(Exception):
    """
    Exception raised when a wallet does not have enough credits for
    discredit operation.
    """
    def __init__(self,
                 wallet_ID,
                 current_amount,
                 discredit_amount):
        self.message = "Tried to discredit `{}` credits from wallet `{}` with only `{}` credits.".format(discredit_amount,
                                                                                                    wallet_ID,
                                                                                                    current_amount)
        super().__init__(self.message)

class Wallet(object):
    """
    Class that handles all functions pertaining to a node's crypto
    wallet.  Objects of this class are never transmitted, but stored
    locally for ease of validating transactions and blocks.
    """
    def __init__(self, ID, credits=0):
        """
        ID: The unique identifier for the node (String)
        credits: Initial amount
        """
        self.credits = Decimal(str(credits))
        self.ID = ID

    def __repr__(self):
        return "Wallet(ID=`{}`, credits={})".format(self.ID, self.credits)
    
    def __credit_amount__(self, credits=0):
        """
        Never call this function from outside the internal scope of the
        object.
        """
        self.credits+=Decimal(str(credits))

    def __discredit_amount__(self, credits=0):
        """
        Never call this function from outside the internal scope of the
        object.        
        """
        self.credits-=Decimal(str(credits))

    def credit_amount(self, credits):
        """
        Use this function to credit the wallet with a certain amount of
        credits
        """
        self.__credit_amount__(credits=credits)

    def discredit_amount(self, credits):
        """
        Use this function to discredit the wallet with a certain amount of
        credits
        """
        if self.credits < credits:
            raise NotEnoughCreditsException(self.ID,
                                            self.credits,
                                            credits)
        self.__discredit_amount__(credits=credits)
