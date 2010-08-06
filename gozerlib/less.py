# gozerlib/less.py
#
#

""" maintain bot output cache. """

# gozerlib imports

from utils.exception import handle_exception
from utils.limlist import Limlist

## classes

class Less(object):

    """
        output cache .. caches upto <nr> item of txt lines per channel.

        :param nr: size of backlog
        :type nr: integer

    """

    def __init__(self, nr):
        self.data = {}
        self.index = {}
        self.nr = nr

    def add(self, channel, listoftxt):
        """
            add listoftxt to channel's output .. set index for used by more 
            commands.

            :param channel: channel to add txt to cache for
            :type channel: string
            :param listoftxt: list of txt to cache
            :type listoftxt: list

        """
        if not self.data.has_key(channel):
            self.data[channel] = Limlist(self.nr)
        self.data[channel].insert(0, listoftxt)
        self.index[channel] = 1

    def get(self, channel, index1, index2):
        """
             return less entry.

             entry is self.data[channel][index1][index2]

             :param channel: channel to get data for
             :type channel: string
             :param index1: number of txtlines back
             :type index1: integer
             :param index2: index into the txtlines 
             :type index2: integer
             :rtype: string

        """

        try:
            txt = self.data[channel][index1][index2]
        except (KeyError, IndexError):
            txt = None
        return txt

    def more(self, channel, index1=0):
        """
             return more entry pointed to by index .. increase index.

             :param channel: channel to fetch data for
             :type channel: string
             :param index1: index into cache data
             :type index1: integer
             :rtype: tuple .. (txt, index)

        """
        try:
            nr = self.index[channel]
        except KeyError:
            nr = 1

        try:
            txt = self.data[channel][index1][nr]
            size = len(self.data[channel][index1])-nr
            self.index[channel] = nr+1
        except (KeyError, IndexError):
            handle_exception()
            txt = None
            size = 1

        return (txt, size-1)

    def size(self, channel):
        """
             return sizes of cached output.

             :param channel: nick to get cache sizes for
             :type channel: string
             :rtype: list .. list of sizes

        """
        sizes = []
        if not self.data.has_key(channel):
            return sizes
        for i in self.data[channel]:
            sizes.append(len(i))

        return sizes
