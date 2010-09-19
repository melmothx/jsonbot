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

## ConsoleEvent class

class ConsoleEvent(EventBase):

    def __deepcopy__(self, a):
        """ deepcopy an console event. """
        e = ConsoleEvent()
        e.copyin(self)
        return e

    def parse(self, bot, input, console, *args, **kwargs):
        """ overload this. """
        if not input: raise NoInput()
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
