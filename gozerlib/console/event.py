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

    def _raw(self, txt):
        """ put rawstring to the server .. overload this """
        logging.info(u"eventbase - out - %s - %s" % (self.userhost, unicode(txt)))
        print u"> " + txt
        self.result.append(txt)  

    def parse(self, input, *args, **kwargs):
        """ overload this. """
        self.auth = getpass.getuser()
        self.userhost = self.auth
        self.origin = self.userhost
        self.txt = input
        self.usercmnd = input.split()[0]
        self.channel = self.userhost
        self.chan = ChannelBase(self.channel)
        self.makeargs()
