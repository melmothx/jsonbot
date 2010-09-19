# gozerbot/morphs.py
#
#

""" convert input/output stream. """

## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.utils.trace import calledfrom

## basic imports

import sys

## Morph claas

class Morph(object):

    """ transform stream. """

    def __init__(self, func):
        self.plugname = calledfrom(sys._getframe(0))
        self.func = func
        self.activate = True

    def do(self, *args, **kwargs):
        """ do the morphing. """
        if not self.activate: return
        try: return self.func(*args, **kwargs)
        except Exception, ex: handle_exception()

class MorphList(list):

    """ list of morphs. """

    def add(self, func, index=None):
        """ add morph. """
        if not index: self.append(Morph(func))
        else: self.insert(index, Moprh(func))
        return self

    def do(self, input, *args, **kwargs):
        """ call morphing chain. """
        for morph in self: input = morph.do(input, *args, **kwargs) or input
        return input

    def unload(self, plugname):
        """ unload morhps belonging to plug <plugname>. """
        for index in range(len(self)-1, -1, -1):
            if self[index].plugname == plugname: del self[index]

    def disable(self, plugname):
        """ disable morhps belonging to plug <plugname>. """
        for index in range(len(self)-1, -1, -1):
            if self[index].plugname == plugname: self[index].activate = False

    def activate(self, plugname):
        """ activate morhps belonging to plug <plugname>. """
        for index in range(len(self)-1, -1, -1):
            if self[index].plugname == plugname: self[index].activate = False

## global morphs

inputmorphs = MorphList()
outputmorphs = MorphList()
