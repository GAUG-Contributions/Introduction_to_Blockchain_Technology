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
validation.py
=======================
Module that validates block transactions
"""
import node_state
import atomic
from decimal import Decimal
from wallet import NotEnoughCreditsException

NEW_NODE_INITIAL_CREDITS = 5

class BlockException(Exception):
    """
    Exception that is raised when TransactionExceptions occur when 
    validating a Block
    """
    def __init__(self, transactionExceptions=[]):
        self.transactionExceptions = transactionExceptions
        super().__init__("Block failed to validate. Following Exceptions occured: {}".format(str(transactionExceptions)))

def apply_block(block, commit=False):
    """
    Try to update node_state based on all the transactions in the
    block.  If commit is False, then it will revert node_state, else
    it will commit node_state
    """
    block_ID = block.compute_hash()
    miner_ID = block.minerID
    memes_upvoted = {}
    errors = []
    
    for trindex, transaction in enumerate(block.transactions):
        # Skip if it is a pseudo transaction (no type field)
        if not(transaction.get("type")):
            continue
            
        ret = None
        try:
            ret = apply_transaction(transaction, block_ID, miner_ID, just_validate=(not commit))
        except TransactionException as Exp:
            Exp.trindex = trindex
            errors.append(Exp)
        if ret is not None: # Which means it was an upvote
                            # transaction, and ret is the memeID of a
                            # meme that was upvoted
            memes_upvoted[ret] = node_state.Memes[ret]

    if errors:
        atomic.revert()
        return False, errors
    if commit:
        for memeID, meme in memes_upvoted.items():
            meme.reward_upvoters(block_ID) # Reward Upvoters that upvoted
                                           # the meme before block
                                           # `block_ID`

    if commit:
        atomic.commit()
    else:
        atomic.revert()

    return True, errors

def apply_transaction(transaction_data, block_ID, miner_ID, just_validate=False):
    """
    Update node_state based on transaction_data
    """
    if transaction_data["type"] == "Upvote":
        return apply_upvote_transaction(transaction_data, block_ID, miner_ID, just_validate=just_validate)
    elif transaction_data["type"] == "Meme":
        apply_meme_transaction(transaction_data, block_ID, miner_ID, just_validate=just_validate)
    elif transaction_data["type"] == "MemeFormat":
        apply_memeFormat_transaction(transaction_data, block_ID, miner_ID, just_validate=just_validate)
    elif transaction_data["type"] == "OwnershipSaleOffer":
        apply_ownership_sale_offer_transaction(transaction_data, block_ID, miner_ID, just_validate=just_validate)
    elif transaction_data["type"] == "OwnershipPurchase":
        apply_ownership_purchase_transaction(transaction_data, block_ID, miner_ID, just_validate=just_validate)


def apply_upvote_transaction(transaction_data, block_ID, miner_ID, just_validate=False):
    """
    Update node_state based on a memeFormat transaction
    """
    node_id = transaction_data["nodeID"]
    print("Validating Upvote : {}".format(str(just_validate)))
    if node_id not in node_state.Nodes:
        raise(NodeNotFoundException(node_id,
                                    transaction_data["upvoteID"]))

    meme_id = transaction_data["imageVoteId"]
    if meme_id not in node_state.Memes:
        raise(MemeNotFoundException(meme_id,
                                    transaction_data["upvoteID"]))
    try:
        new_upvote = node_state.Upvote(transaction_data["upvoteID"],
                                       meme_id,
                                       node_id,
                                       block_ID,
                                       miner_ID,
                                       discredit_only = just_validate)
    except NotEnoughCreditsException as Exp:
        raise UpvoteFailedNoCreditsException(node_id,
                                             transaction_data["upvoteID"],
                                             Exp.message)
    return meme_id

def apply_memeFormat_transaction(transaction_data, block_ID, miner_ID, just_validate=True):
    """
    Update node_state based on a memeFormat transaction
    """
    node_id = transaction_data["nodeID"]
    node = None
    if just_validate:
        # print(just_validate)
        return
    print("Creating MemeFormat")
    if node_id not in node_state.Nodes: #Means the node is new. Start
                                        #tracking the state of this
                                        #node
        node = node_state.Node(node_id, NEW_NODE_INITIAL_CREDITS)
    else:
        node = node_state.Nodes[node_id]

    memeFormat = node_state.MemeFormat(transaction_data["imageId"],
                                       transaction_data["name"],
                                       "Sample Description",
                                       transaction_data["zEncoding64_val"],
                                       node_id,
                                       miner_ID)

def apply_meme_transaction(transaction_data, block_ID, miner_ID, just_validate=False):
    """
    Update node_state based on a meme transaction
    """
    node_id = transaction_data["nodeID"]
    node = None

    if transaction_data["memeFormat"] not in node_state.MemeFormats:
        raise(MemeFormatNotFoundException(transaction_data["memeFormat"],
                                          transaction_data["imageId"]))
    if just_validate:
        return
    print("Creating Meme")
    if node_id not in node_state.Nodes: # Means the node is new. Start
                                        # tracking the state of this
                                        # node
        node = node_state.Node(node_id, NEW_NODE_INITIAL_CREDITS)
    else:
        node = node_state.Nodes[node_id]

    meme = node_state.Meme(transaction_data["imageId"],
                           transaction_data["name"],
                           transaction_data["memeFormat"],
                           transaction_data["zEncoding64_val"],
                           transaction_data["nodeID"],
                           block_ID,
                           miner_ID)

def apply_ownership_sale_offer_transaction(transaction_data, block_ID, miner_ID, just_validate=False):
    """
    Update node_state based on a ownership sale offer transaction
    """
    node_id = transaction_data["nodeID"]

    if transaction_data["memeFormat"] not in node_state.MemeFormats:
        raise(MemeFormatNotFoundException(transaction_data["memeFormat"],
                                          transaction_data["ownershipSaleOfferID"]))

    if node_id not in node_state.Nodes:
        raise NodeNotFoundException(node_id, transaction_data["ownershipSaleOfferID"])

    if transaction_data["memeFormat"] not in node_state.Nodes[node_id].meme_formats:
        raise MemeFormatNotOwnedByNodeException(node_id,
                                                transaction_data["memeFormat"],
                                                transaction_data["ownershipSaleOfferID"])

    if node_state.MemeFormats[transaction_data["memeFormat"]].ownership_sales and node_state.MemeFormats[transaction_data["memeFormat"]].ownership_sales[-1].buyerID is None:
        raise(MemeFormatHasPendingSaleOfferException(transaction_data["memeFormat"],
                                                     transaction_data["ownershipSaleOfferID"]))

    if Decimal(transaction_data["saleAmount"]) <= 0:
        raise OwnershipSaleAmountNotPositiveException(transaction_data["ownershipSaleOfferID"],
                                                      transaction_data["saleAmount"],
                                                      transaction_data["ownershipSaleOfferID"])
    
    if just_validate:
        return

    print("Creating Ownership Sale Offer")

    node_state.OwnershipSaleOffer(transaction_data["ownershipSaleOfferID"],
                                  node_id,
                                  transaction_data["memeFormat"],
                                  block_ID,
                                  miner_ID,
                                  amount=transaction_data["saleAmount"])
    
def apply_ownership_purchase_transaction(transaction_data, block_ID, miner_ID, just_validate=False):
    """
    Update node_state based on a ownership purchase transaction
    """
    node_id = transaction_data["nodeID"]
    
    if node_id not in node_state.Nodes:
        raise NodeNotFoundException(node_id, transaction_data["ownershipPurchaseID"])
    
    if transaction_data["ownershipSaleOfferID"] not in node_state.OwnershipSaleOffers:
        raise(OwnershipSaleOfferNotFoundException(transaction_data["ownershipSaleOfferID"],
                                                  transaction_data["ownershipPurchaseID"]))
    
    if node_state.OwnershipSaleOffers[transaction_data["ownershipSaleOfferID"]].buyerID is not None:
        raise OwnershipSaleOfferAlreadyAcceptedException(transaction_data["ownershipSaleOfferID"],
                                                         node_state.OwnershipSaleOffers[transaction_data["ownershipSaleOfferID"]].buyerID,
                                                         node_state.OwnershipSaleOffers[transaction_data["ownershipSaleOfferID"]].buyerBlockID,
                                                         transaction_data["ownershipPurchaseID"])

    try:
        node_state.OwnershipSaleOffers[transaction_data["ownershipSaleOfferID"]].buy(node_id,
                                                                                     block_ID,
                                                                                     miner_ID,
                                                                                     discredit_only=just_validate)
    except NotEnoughCreditsException as Exp:
        raise OwnershipPurchaseFailedNoCreditsException(node_id,
                                                        node_state.OwnershipSaleOffers[transaction_data["ownershipSaleOfferID"]].memeFormatID,
                                                        transaction_data["ownershipPurchaseID"],
                                                        Exp.message)


class TransactionException(Exception):
    """
    Exception raised when an exception occurs validating a transaction
    """
    def __init__(self, transactionID, message):
        self.transactionID = transactionID
        super().__init__("Error in transaction `{}`. {}".format(self.transactionID, message))
class MemeFormatNotFoundException(TransactionException):
    """
    Exception raised when the specified MemeFormat is not found in node_state
    """
    def __init__(self, memeFormatID, transactionID):
        super().__init__(transactionID, "MemeFormat `{}` not found".format(memeFormatID))
class MemeNotFoundException(TransactionException):
    """
    Exception raised when the specified Meme is not found in node_state
    """
    def __init__(self, memeID, transactionID):
        super().__init__(transactionID, "Meme `{}` not found".format(memeID))
class NodeNotFoundException(TransactionException):
    """
    Exception raised when the specified Node is not found in node_state
    """
    def __init__(self, nodeID, transactionID):
        super().__init__(transactionID, "Node `{}` not found".format(nodeID))
class UpvoteFailedNoCreditsException(TransactionException):
    """
    Exception raised when Upvote transaction fails to proceed due to
    the upvoter not having enough credits.
    """
    def __init__(self, nodeID, transactionID, message):
        super().__init__(transactionID,
                       "{}. Node `{}` does not have enough credits for Upvote".format(message,
                                                                                      nodeID))
class MemeFormatNotOwnedByNodeException(TransactionException):
    """
    Exception raised when a node attempts to sell ownership to a
    MemeFormat that it does not own
    """
    def __init__(self, nodeID, memeFormatID, transactionID):
        super().__init__(transactionID,
                         "MemeFormat `{}` is not owned by Node `{}`".format(memeFormatID, nodeID))
class OwnershipSaleOfferAlreadyAcceptedException(TransactionException):
    """
    Exception raised when node attempts to buy ownership based on a
    ownership sale offer that was already accepted
    """
    def __init__(self, ownershipSaleOfferID, nodeID, blockID, transactionID):
        super().__init__(transactionID,
                         "The Ownership Sale Offer `{}` has already been accepted and ownership has been assigned to Node `{}` in block `{}`".format(ownershipSaleOfferID, nodeID, blockID))
class OwnershipSaleAmountNotPositiveException(TransactionException):
    """
    Exception raised when OwnershipSaleOffer amount is non-positive
    """
    def __init__(self, ownershipSaleOfferID, saleAmount,transactionID):
        super().__init__(transactionID,
                         "The saleAmount `{}` for Ownership Sale Offer `{}` is non positive".format(saleAmount,ownershipSaleOfferID))
class MemeFormatHasPendingSaleOfferException(TransactionException):
    """
    Exception raised when a node tries to add an Ownership Sale offer
    when their previous offer for the same MemeFormat is still
    pending, and has no buyer.
    """
    def __init__(self, memeFormatID, transactionID):
        super().__init__(transactionID,
                         "The MemeFormat `{}` still has a pending Ownership Sale Offer".format(memeFormatID))
class OwnershipSaleOfferNotFoundException(TransactionException):
    """
    Exception raised when Ownership Sale Offer is not found in node_state
    """
    def __init__(self, ownershipSaleOfferID, transactionID):
        super().__init__(transactionID,
                         "The Ownership Sale Offer `{}` was not found.".format(ownershipSaleOfferID))
class OwnershipPurchaseFailedNoCreditsException(TransactionException):
    """
    Exception raised when OwnershipPurchase fails due to the buyer not
    having enough credits
    """
    def __init__(self, nodeID, memeFormatID, transactionID, message):
        super().__init__(transactionID,
                       "{}. Node `{}` does not have enough credits for Purchasing Ownership in MemeFormat `{}`".format(message,
                                                                                                                       nodeID,
                                                                                                                       memeFormatID))
