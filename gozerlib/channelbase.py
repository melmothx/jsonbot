# gozerlib/channelbase.py
#
#

""" provide a base class for channels (waves, xmpp, web). """

## gozerlib imports

from gozerlib.utils.lazydict import LazyDict
from gozerlib.persist import Persist

## basic imports

import time

class ChannelBase(Persist):

    """
        Base class for all channel objects. 

        :param name: name of the channel
        :type name: string
        :param type: type of channel
        :type type: string

    """

    def __init__(self, id, type="notset"):
        Persist.__init__(self, id)
        self.id = id
        self.type = type
        self.lastmodified = time.time()
        self.data.feeds = self.data.feeds or []
        self.data.passwords = self.data.passwords or {}

    def setpass(self, name, key):
        self.data.passwords[name] = key
        self.save()

    def getpass(self, name='IRC'):
        try:
            return self.data.passwords[name]
        except KeyError:
            return

    def delpass(self, name='IRC'):
        try:
            del self.data.passwords[name]
            self.save()
            return True
        except KeyError:
            return

    def parse(self, event, wavelet=None):

        """
            parse an event for channel related data and constuct the 
            channel with it. Overload this.

            :param event: event to parse
            :type event: gozerlib.eventbase.EventBase
            :rtype: self

        """

        pass

