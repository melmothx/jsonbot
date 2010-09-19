# gozerlib/less.py
#
#

""" maintain bot output cache. """

# gozerlib imports

from utils.exception import handle_exception
from utils.limlist import Limlist

## Less class

class Less(object):

    """ output cache .. caches upto <nr> item of txt lines per channel. """

    def __init__(self, nr):
        self.data = {}
        self.nr = nr

    def clear(self, channel):
        """ clear outcache of channel. """
        channel = unicode(channel).lower()
        try: del self.data[channel]
        except KeyError: pass

    def add(self, channel, listoftxt):
        """ add listoftxt to channel's output. """
        channel = unicode(channel).lower()
        if not self.data.has_key(channel): self.data[channel] = []
        self.data[channel].extend(listoftxt)

    def set(self, channel, listoftxt):
        """ set listoftxt to channel's output. """
        channel = unicode(channel).lower()
        self.data[channel] = listoftxt

    def get(self, channel):
        """ return 1 item popped from outcache. """
        channel = unicode(channel).lower()
        try: txt = self.data[channel].pop(0)
        except (KeyError, IndexError): txt = None
        return txt

    def more(self, channel):
        """ return more entry and remaining size. """
        channel = unicode(channel).lower()
        txt = self.get(channel)
        try: size = len(self.data[channel])
        except (KeyError, IndexError):
            txt = None
            size = 0
        return (txt, size)

    def size(self, channel):
        """ return sizes of cached output. """
        channel = unicode(channel).lower()
        sizes = []
        if not self.data.has_key(channel): return sizes
        if self.data[channel]: return len(self.data[channel])
        return 0
