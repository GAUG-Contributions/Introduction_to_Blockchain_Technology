from wallet import Wallet
from atomic import Atomic
from collections import defaultdict
Nodes = {}
MemeFormats = {}
Memes = {}
Upvotes = {}

UPVOTE_REWARD = 0.10 # Percentage, (in the form of a fraction) of
                     # upvote credits rewarded to upvoters from
                     # previous block.

MEME_POSTER_PORTION = 0.60 #Percentage, (in the form of a fraction) of
                           #upvote credits claimed by node that posted
                           #meme.

MEME_MINER_PORTION = 0.10 #Percentage, (in the form of a fraction) of
                          #upvote credits claimed by node that mined
                          #the meme.

MEME_FORMAT_OWNER_PORTION = 0.30 #Percentage, (in the form of a fraction) of
                          #upvote credits claimed by meme owner.

MEME_FORMAT_MINER_REWARD = 0.10 # Percentage, (in the form of a
                                # fraction) of upvote credits
                                # rewarded to the miner who mined to
                                # MemeFormat

UPVOTE_MINER_REWARD = 0.10 #Percentage, (in the form of a fraction) of
                           #upvote credits rewarded to miner who mined
                           #the upvote.

class Node(Atomic):
    """
    Class that handles all functions pertaining to maintaining state
    of a Node.
    """
    def __init__(self, ID, credits):
        self.ID = ID
        self.wallet = Wallet(ID, credits=credits)
        if self.ID not in Nodes:
            Nodes[ID] = ID
        else:
            pass
        #TODO: Throw an exception

        self.meme_formats = {}
        self.memes = {}
        self.upvotes = {}
        
        super.__init__()

    def __repr__(self):
        return "ID=`{}`, Wallet={}".format(self.ID, str(self.wallet))
        

    def add_meme_format(self, meme_format_ID):
        """
        Add a Meme format to the Node
        ownership : percentage of ownership of meme_format
        """
        self.meme_formats[meme_format_ID] = MemeFormats[meme_format_ID]

    def add_meme(self, meme_ID):
        """
        Add a meme to the node
        """
        self.memes[meme_ID] = Memes[meme_ID]

    def add_upvote(self, upvote_ID):
        """
        Add an upvote to the node
        """
        self.upvotes[upvote_ID] = Upvotes[upvote_ID]

class MemeFormat(Atomic):
    """
    Class that handles all functions pertaining to maintaining state
    of a MemeFormat.
    """
    def __init__(self, ID, name, description, binary, owner):
        """
        ID : Uniquely Identifiable ID for the MemeFormat
        name : Any Display Name for the MemeFormat
        description : Some textual description of the MemeFormat
        binary : binary data of a meme example, possible related 
                 to the description
        owner : ID(s) of the node(s) that own the MemeFormat
        miner : ID(s) of the node that mined the MemeFormat
        """
        self.ID, self.name, self.description, self.binary, self.owner, self.miner = ID, name, description, binary, owner, miner

        if self.ID not in MemeFormats:
            MemeFormats[self.ID] = self
        else:
            pass
        #TODO : Throw Exception
        
        self.memes = {}
        super.__init__()

        Nodes[self.owner].add_meme_format(self.ID)

    def add_meme(self, meme_ID):
        """
        Add meme to MemeFormat
        """
        self.memes[meme_ID] = Memes[meme_ID]

class Meme(Atomic):
    """
    Class that handles all functions pertaining to maintaining state
    of a Meme.
    """
    def __init__(self, ID, title, meme_format, binary, poster_ID, block_ID, miner_ID, extension="jpg" ):
        """
        ID : Uniquely identifiable ID for the Meme
        title : Some string Title for the Meme
        meme_format : ID of the meme_format
        binary : binary bits of the meme
        poster_ID : ID of node that posted meme
        block_ID : ID of block which contains the transaction 
                   posting the meme
        miner_ID : ID of miner node who created the block with block_ID
        """
        self.ID, self.title, self.meme_format, self.binary, self.poster_ID, self.block_ID, self.miner_ID, self.extension = ID, title, meme_format, binary, poster_ID, block_ID, miner_ID, extension

        if self.ID not in Memes:
            Memes[self.ID] = self
        else:
            pass
            #TODO : Throw exception

        self.blocks = defaultdict(dict)
        self.blocklist = []
        self.upvote_credits = defaultdict(lambda:0)


        super.__init__()
        
        MemeFormats[meme_format].add_meme(self.ID)
        Nodes[poster_ID].add_meme(self.ID)

    def add_upvote(self, upvote_ID):
        upvote = Upvotes[upvote_ID]
        block_ID = upvote[block_ID]

        if block_ID not in self.blocklist:
            self.blocklist.append(block_ID) # Add block_ID to
                                            # blocklist if it's the
                                            # first upvote
        self.blocks[block_ID][upvote_ID] = upvote # add upvote to
                                                  # block
        self.upvote_credits[block_ID]+=upvote.credits

    def reward_upvoters(self, block_ID):
        """
        Reward upvoters who upvoted before block `block_ID`.  All upvotes
        in the block should already be added using Meme.add_upvote
        """
        reward_amount = self.upvote_credits[block_ID] * UPVOTE_REWARD

        for block_id in self.blocklist:
            if block_id == block_ID: 
                break # Stop rewarding after all blocks before `block_ID` have been processed
            for upvote_ID, upvote in self.blocks[block_id].items():
                Nodes[upvote.upvoter_ID].wallet.credit_amount(reward_amount)

class Upvote(Atomic):
    """
    Class that handles all the functions pertaining to maintaining state
    of an Upvote
    """
    def __init__(self, ID, meme_ID, upvoter_ID, block_ID, miner_ID, credits=1):
        """
        Initializes the upvote and transfers appropriate credits to meme
        poster, MemeFormat owner. Also rewards the UpvoteMiner,
        MemeMiner, MemeFormatMiner

        """
        self.ID, self.meme_ID, self.upvoter_ID, self.block_ID, self.miner_ID, self.credits = ID, meme_ID, upvoter_ID, block_ID, miner_ID, credits

        if self.ID not in Upvotes:
            Upvotes[self.ID] = self
        else:
            pass
        #TODO : Throw exception

        Nodes[self.upvoter_ID].add_upvote(self.ID)
        Memes[self.meme_ID].add_upvote(self.ID)

        super.__init__()

        meme_poster_id = Memes[self.meme_ID].poster_ID
        meme_miner_id = Memes[self.meme_ID].miner_ID
        meme_format_owner_id = MemeFormats[Memes[self.meme_ID].meme_format].owner
        
        meme_format_miner_id = MemeFormats[Memes[self.meme_ID].meme_format].miner
        
        Nodes[upvoter_ID].wallet.discredit_amount(self.credits)
        
        Nodes[meme_poster_id].wallet.credit_amount(self.credits * MEME_POSTER_PORTION) # Credit Meme Poster
        Nodes[meme_miner_id].wallet.credit_amount(self.credits * MEME_MINER_PORTION)# Credit Meme Miner
        Nodes[meme_format_owner_id].wallet.credit_amount(self.credits * MEME_FORMAT_OWNER_PORTION)# Credit MemeFormat Owner

        Nodes[meme_format_miner_id].wallet.credit_amount(self.credits * MEME_FORMAT_MINER_REWARD)# Reward MemeFormat Miner
        Nodes[self.miner_ID].wallet.credit_amount(self.credits * UPVOTE_MINER_REWARD)# Reward Upvote Miner
