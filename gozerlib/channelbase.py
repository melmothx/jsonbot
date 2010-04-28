# gozerlib/channelbase.py
#
#

""" provide a base class for channels (waves, xmpp, web). """

## gozerlib imports

from gozerlib.utils.lazydict import LazyDict
from gozerlib.persist import Persist

## basic imports

import time

## classes

class ChannelBase(Persist):

    """
        Base class for all channel objects. 

        :param id: id of the channel
        :type id: string
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

    def setpass(self, type, key):
        """ set channel password based on type. """
        self.data.passwords[type] = key
        self.save()

    def getpass(self, type='IRC'):
        """ get password based of type. """
        try:
            return self.data.passwords[type]
        except KeyError:
            return

    def delpass(self, type='IRC'):
        """ delete password. """
        try:
            del self.data.passwords[type]
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
            :param wavelet: wavelet to parse with
            :type wavelet: waveap.wavelet.Wavelet
            :rtype: self

        """
        pass
