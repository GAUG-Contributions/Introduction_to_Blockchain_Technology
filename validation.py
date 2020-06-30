import node_state
import atomic
from wallet import NotEnoughCreditsException

NEW_NODE_INITIAL_CREDITS = 5

class BlockException(Exception):
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

def apply_upvote_transaction(transaction_data, block_ID, miner_ID, just_validate=False):
    """
    Update node_state based on a memeFormat transaction
    """
    node_id = transaction_data["nodeID"]
    print("Validating Upvote : {}".format(str(just_validate)))
    if node_id not in node_state.Nodes:
        raise(NodeNotFoundForUpvoteException(node_id,
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

class TransactionException(Exception):
    def __init__(self, transactionID, message):
        self.transactionID = transactionID
        super().__init__("Error in transaction `{}`. {}".format(self.transactionID, message))

class MemeFormatNotFoundException(TransactionException):
    def __init__(self, memeFormatID, transactionID):
        super().__init__(transactionID, "MemeFormat `{}` not found".format(memeFormatID))

class MemeNotFoundException(TransactionException):
    def __init__(self, memeID, transactionID):
        super().__init__(transactionID, "Meme `{}` not found".format(memeID))

class NodeNotFoundForUpvoteException(TransactionException):
    def __init__(self, nodeID, transactionID):
        super().__init__(transactionID, "Node `{}` not found".format(nodeID))

class UpvoteFailedNoCreditsException(TransactionException):
    def __init__(self, nodeID, transactionID, message):
        super().__init__(transactionID,
                       "{}. Node `{}` does not have enough credits for Upvote".format(message,
                                                                                      nodeID))
