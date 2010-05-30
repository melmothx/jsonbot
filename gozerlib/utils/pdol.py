# gozerbot/pdol.py
#
#

""" pickled dict of lists """

__copyright__ = 'this file is in the public domain'

from gozerlib.persist import Persist
 
class Pdol(Persist):

    """ pickled dict of lists """

    def __init__(self, fname):
        Persist.__init__(self, fname)
        if not self.data:
            self.data = {}

    def __iter__(self, name):
        return self.data[name].__iter__()
 
    def __getitem__(self, item):
        if self.data.has_key(item):
            return self.data[item]

    def __delitem__(self, item):
        if self.data.has_key(item):
            self.data.__delitem__(item)
            return 1

    def __setitem__(self, item, what):
        self.data[item] = what
        return self

    def add(self, item, what):
        """ add what to items list """
        return self.__setitem__(item, what)

    def adduniq(self, item, what):
        """ add what to items list if item not yet added """
        if not self.data.has_key(item):
            self.new(item)
        if what not in self.data[item]:
            return self.__setitem__(item, what)

    def get(self, item):
        """ get items list """
        return self.__getitem__(item)

    def new(self, what):
        """ reset list of what """
        self.data[what] = []

    def delete(self, item, what):
        """ remove what from item's list """
        del self.data[item][what]

    def extend(self, item, what):
        if not self.data.has_key(item):
            self.new(item)
        self.data[item].extend(what)

    def remove(self, item, what):
        try:
            self.data[item].remove(what)
            return 1
        except (ValueError, KeyError):
            return 0
