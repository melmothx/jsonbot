# gozerlib/less.py
#
#

""" maintain bot output cache. """

# gozerlib imports

from utils.limlist import Limlist

## classes

class Less(object):

    """
        output cache .. caches upto <nr> item of txt lines per nick.

        :param nr: size of backlog
        :type nr: integer

    """

    def __init__(self, nr):
        self.data = {}
        self.index = {}
        self.nr = nr

    def add(self, nick, listoftxt):
        """
            add listoftxt to nick's output .. set index for used by more 
            commands.

            :param nick: nick to add txt to cache for
            :type nick: string
            :param listoftxt: list of txt to cache
            :type listoftxt: list

        """
        if not self.data.has_key(nick):
            self.data[nick] = Limlist(self.nr)
        self.data[nick].insert(0, listoftxt)
        self.index[nick] = 1

    def get(self, nick, index1, index2):
        """
             return less entry.

             entry is self.data[nick][index1][index2]

             :param nick: nick to get data for
             :type nick: string
             :param index1: number of txtlines back
             :type index1: integer
             :param index2: index into the txtlines 
             :type index2: integer
             :rtype: string

        """

        try:
            txt = self.data[nick][index1][index2]
        except (KeyError, IndexError):
            txt = None
        return txt

    def more(self, nick, index1):
        """
             return more entry pointed to by index .. increase index.

             :param nick: nick to fetch data for
             :type nick: string
             :param index1: index into cache data
             :type index1: integer
             :rtype: tuple .. (txt, index)

        """
        try:
            nr = self.index[nick]
        except KeyError:
            nr = 1

        try:
            txt = self.data[nick][index1][nr]
            size = len(self.data[nick][index1])-nr
            self.index[nick] = nr+1
        except (KeyError, IndexError):
            txt = None
            size = 0

        return (txt, size-1)

    def size(self, nick):
        """
             return sizes of cached output.

             :param nick: nick to get cache sizes for
             :type nick: string
             :rtype: list .. list of sizes

        """
        sizes = []
        if not self.data.has_key(nick):
            return sizes
        for i in self.data[nick]:
            sizes.append(len(i))

        return sizes
