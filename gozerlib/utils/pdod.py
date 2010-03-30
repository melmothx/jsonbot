# gozerbot/pdod.py
#
#

""" pickled dicts of dicts """

__copyright__ = 'this file is in the public domain'

from gozerlib.utils.lazydict import LazyDict
from gozerlib.utils.locking import lockdec
from gozerlib.persist import Persist

import thread

pdodlock = thread.allocate_lock()
locked = lockdec(pdodlock)
 
class Pdod(Persist):

    """ pickled dicts of dicts """

    def __init__(self, filename):
        Persist.__init__(self, filename)
        if not self.data:
            self.data = LazyDict()

    def __getitem__(self, name):
        """ return item with name """
        if self.data.has_key(name):
            return self.data[name]

    #@locked
    def save(self):
        Persist.save(self)

    #@locked
    def __delitem__(self, name):
        """ delete name item """
        if self.data.has_key(name):
            return self.data.__delitem__(name)

    #@locked
    def __setitem__(self, name, item):
        """ set name item """
        self.data[name] = item

    def __contains__(self, name):
        return self.data.__contains__(name)

    #@locked
    def setdefault(self, name, default):
        """ set default of name """
        return self.data.setdefault(name, default)

    def has_key(self, name):
        """ has name key """
        return self.data.has_key(name)

    def has_key2(self, name1, name2):
        """ has [name1][name2] key """
        if self.data.has_key(name1):
            return self.data[name1].has_key(name2)

    def get(self, name1, name2):
        """ get data[name1][name2] """
        try:
            result = self.data[name1][name2]
            return result
        except KeyError:
            return None

    #@locked
    def set(self, name1, name2, item):
        """ set name, name2 item """
        if not self.data.has_key(name1):
            self.data[name1] = {}
        self.data[name1][name2] = item
