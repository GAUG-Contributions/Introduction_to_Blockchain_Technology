import copy
__initialized_objects__ = []

__branched__ = False
class Atomic(object):
    def __init__(self):
        global __initialized_objects__
        self.__var_backup__ = {}
        self.__committed_once__ = False
        __initialized_objects__.append(self)

    def commit(self):
        self.__committed_once__ = True
        self.__var_backup__ = copy.deepcopy(dict(vars(self)))
        self.__var_backup__.pop("__var_backup__")

    def revert(self):
        for attr, val in self.__var_backup__.items():
            setattr(self, attr, val)

def commit():
    for atomic_object in __initialized_objects__:
        if hasattr(atomic_object, "wallet"):
            print(atomic_object.ID, atomic_object.wallet.credits)
        atomic_object.commit()

def revert():
    for atomic_object in __initialized_objects__:
        if not atomic_object.__committed_once__:
            __initialized_objects__.remove(atomic_object)
            del atomic_object
        elif hasattr(atomic_object, "wallet"):
            print(atomic_object.ID, atomic_object.wallet.credits, "Reverting to {}".format(atomic_object.__var_backup__["wallet"].credits))
            atomic_object.revert()
        else:
            atomic_object.revert()

