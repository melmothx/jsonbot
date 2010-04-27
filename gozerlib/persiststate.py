# gozerlib/persiststate.py
#
#

""" persistent state classes. """

## gozerlib imports

from gozerlib.utils.name import stripname
from gozerlib.utils.trace import calledfrom
from persist import Persist

## basic imports

import types
import os
import sys
import logging

class PersistState(Persist):

    """ base persitent state class. """

    def __init__(self, filename):
        Persist.__init__(self, filename)
        self.types = dict((i, type(j)) for i, j in self.data.iteritems())

    def __getitem__(self, key):

        """ get state item. """

        return self.data[key]

    def __setitem__(self, key, value):

        """ set state item. """

        self.data[key] = value

    def define(self, key, value):

        """ define a state item. """

        if not self.data.has_key(key) or type(value) != self.types[key]:

            if type(value) == types.StringType:
                value = unicode(value)

            if type(value) == types.IntType:
                value = long(value)

            self.data[key] = value

class PlugState(PersistState):

    """ state for plugins. """

    def __init__(self, *args, **kwargs):
        self.plugname = calledfrom(sys._getframe())
        logging.debug('persiststate - initialising %s' % self.plugname)
        PersistState.__init__(self, 'gozerdata' + os.sep + 'state' + os.sep + 'plugs' + os.sep + self.plugname + os.sep + 'state')

class ObjectState(PersistState):

    """ state for usage in constructors. """

    def __init__(self, *args, **kwargs):
        PersistState.__init__(self, 'gozerdata' + os.sep + 'state' + os.sep + calledfrom(sys._getframe(1))+'.state')

class UserState(PersistState):

    """ state for users. """

    def __init__(self, username, filename="state", *args, **kwargs):
        assert username
        username = stripname(username)
        datadir = 'gozerdata' + os.sep + 'state' + os.sep + 'users' + os.sep + username
        PersistState.__init__(self,  datadir + os.sep + filename)
