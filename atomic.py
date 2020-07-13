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
atomic.py
===================
Module that makes allows for changing the instance variables of multiple objects in one psuedo `atomic` operation.
"""
import copy
__initialized_objects__ = []


__branched__ = False

class Atomic():
    """
    Class that implements the psuedo 'atomic' operations of objects
    """
    def __init__(self):
        global __initialized_objects__
        self.__var_backup__ = {}
        self.__committed_once__ = False
        __initialized_objects__.append(self)

    def commit(self):
        """
        Commit state of object's instance variables into the __var_backup__
        """
        self.__committed_once__ = True
        self.__var_backup__ = copy.deepcopy(dict(vars(self)))
        self.__var_backup__.pop("__var_backup__")

    def revert(self):
        """
        Revert state of object's instance variables to values stored in
        the __var_backup__
        """
        for attr, val in self.__var_backup__.items():
            setattr(self, attr, val)

def commit():
    """
    Commit all objects currently tracked by the
    __initialized_objects__ list
    """
    for atomic_object in __initialized_objects__:
        if hasattr(atomic_object, "wallet"):
            print(atomic_object.ID, atomic_object.wallet.credits)
        atomic_object.commit()

def revert():
    """
    Revert all objects currently tracked by the
    __initialized_objects__ list
    """
    for atomic_object in __initialized_objects__:
        if not atomic_object.__committed_once__:
            __initialized_objects__.remove(atomic_object)
            del atomic_object
        elif hasattr(atomic_object, "wallet"):
            print(atomic_object.ID, atomic_object.wallet.credits, "Reverting to {}".format(atomic_object.__var_backup__["wallet"].credits))
            atomic_object.revert()
        else:
            atomic_object.revert()
