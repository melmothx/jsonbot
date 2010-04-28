# gozerbot/morphs.py
#
#

""" convert input/output stream. """

## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.utils.trace import calledfrom

## basic imports

import sys

## classes

class Morph(object):

    """
        transform stream.

        :param func: morphing function
        :type func: function

    """

    def __init__(self, func):
        self.plugname = calledfrom(sys._getframe(0))
        self.func = func
        self.activate = True

    def do(self, *args, **kwargs):
        """ do the morphing. """
        if not self.activate:
            return

        try:
            return self.func(*args, **kwargs)
        except Exception, ex:
            handle_exception()

class MorphList(list):

    """ list of morphs. """

    def add(self, func, index=None):
        """
            add morph.

            :param func: morphing function
            :type func: function
            :param index: index into the morphlist
            :type index: integer
            :rtype: self

        """
        if not index:
            self.append(Morph(func))
        else:
            self.insert(index, Moprh(func))

        return self

    def do(self, input, *args, **kwargs):
        """
            call morphing chain.

            :param input: data to do the morphing on
            :type input: string

        """
        for morph in self:
            input = morph.do(input, *args, **kwargs) or input

        return input

    def unload(self, plugname):
        """
            unload morhps belonging to plug <plugname>.

            :param plugname: the plugname to unload the morphs from
            :type plugname: string

        """
        for index in range(len(self)-1, -1, -1):
            if self[index].plugname == plugname:
                del self[index]

    def disable(self, plugname):
        """ disable morhps belonging to plug <plugname>. """

        for index in range(len(self)-1, -1, -1):
            if self[index].plugname == plugname:
                self[index].activate = False

    def activate(self, plugname):
        """ activate morhps belonging to plug <plugname>. """
        for index in range(len(self)-1, -1, -1):
            if self[index].plugname == plugname:
                self[index].activate = False

## defines

# moprhs used on input
inputmorphs = MorphList()

# morphs used on output
outputmorphs = MorphList()
