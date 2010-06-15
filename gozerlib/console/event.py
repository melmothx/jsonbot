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
        logging.info("console - out - %s - %s" % (self.userhost, str(resp)))
        self.bot._raw(resp)
        self.result.append(resp)  
        self.outqueue.put_nowait(resp)
        self.bot.outmonitor(self.origin, self.printto, resp, self)

    def _raw(self, txt):
        """ put rawstring to the server .. overload this """
        self.console.push(u"=> " + unicode(txt))

    def parse(self, bot, input, console, *args, **kwargs):
        """ overload this. """
        if not input:
            raise NoInput()
        self.bot = bot
        self.console = console
        self.auth = getpass.getuser() + '@' + bot.uuid
        self.userhost = self.auth
        self.origin = self.userhost
        self.txt = input
        self.usercmnd = input.split()[0]
        self.channel = self.userhost
        self.chan = ChannelBase(self.channel)
        self.cbtype = self.cmnd = unicode("CONSOLE")
        self.makeargs()
