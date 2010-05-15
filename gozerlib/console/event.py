# gozerlib/console/event.py
#
#

""" a console event. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.channelbase import ChannelBase

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

    def reply(self, txt, result=[]):
        if self.checkqueues(result):
             return
        resp = self.makeresponse(txt, result)
        logging.info(u"console - out - %s - %s" % (self.userhost, unicode(resp)))
        self.bot._raw(resp)
        self.result.append(resp)  
        self.outqueue.put_nowait(resp)

    def _raw(self, txt):
        """ put rawstring to the server .. overload this """
        print u"=> " + txt

    def parse(self, bot, input, *args, **kwargs):
        """ overload this. """
        self.bot = bot
        self.auth = getpass.getuser()
        self.userhost = self.auth
        self.origin = self.userhost
        self.txt = input
        self.usercmnd = input.split()[0]
        self.channel = self.userhost
        self.chan = ChannelBase(self.channel)
        self.makeargs()
