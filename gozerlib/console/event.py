# gozerlib/console/event.py
#
#

""" a console event. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.channelbase import ChannelBase
from gozerlib.errors import NoInput

## basic imports

import getpass
import logging
import re

## classes

class ConsoleEvent(EventBase):

    def __deepcopy__(self, a):
        """ deepcopy an console event. """
        e = ConsoleEvent()
        e.copyin(self)
        return e

    def reply(self, txt, result=[], dot=", ", *args, **kwargs):
        if self.checkqueues(result):
             return
        resp = self.makeresponse(txt, result, dot)
        logging.debug("console - out - %s - %s" % (self.userhost, str(resp)))
        self._raw(resp)
        self.result.append(resp)  
        self.outqueue.put_nowait(resp)
        self.bot.outmonitor(self.origin, self.channel, resp, self)

    def _raw(self, txt):
        """ put rawstring to the server .. overload this """
        txt = self.bot.normalize(txt)
        self.console.write(u"\n%s --> %s" % (self.txt, unicode(txt)) + "\n")
        
    def parse(self, bot, input, console, *args, **kwargs):
        """ overload this. """
        if not input:
            raise NoInput()
        self.bot = bot
        self.console = console
        self.nick = getpass.getuser()
        self.auth = self.nick + '@' + bot.uuid
        self.userhost = self.auth
        self.origin = self.userhost
        self.txt = input
        self.usercmnd = input.split()[0]
        self.channel = self.userhost
        self.chan = ChannelBase(self.channel)
        self.cbtype = self.cmnd = unicode("CONSOLE")
        self.makeargs()

    def write(self, txt, *args):
        self._raw(txt)