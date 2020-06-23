class NotEnoughCreditsException(Exception):
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
        self.credits = credits
        self.ID = ID

    def __repr__(self):
        return "Wallet(ID=`{}`, credits={})".format(self.ID, self.credits)
    
    def __credit_amount__(self, credits=0):
        """
        Never call this function from outside the internal scope of the
        object.
        """
        self.credits+=credits

    def __discredit_amount__(self, credits=0):
        """
        Never call this function from outside the internal scope of the
        object.        
        """
        self.credits-=credits

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
