# gozerlib/socklib/xmpp/presence.py
#
#

""" Presence. """

# gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.utils.trace import whichmodule
from gozerlib.gozerevent import GozerEvent

## basic imports

import time
import logging 

## classes

class Presence(GozerEvent):

    def __init__(self, nodedict={}):
        GozerEvent.__init__(self, nodedict)
        self.element = "presence"
        self.jabber = True
        self.cmnd = "PRESENCE"
        self.cbtype = "PRESENCE"
        self.bottype = "xmpp"

    def parse(self):
        """ set ircevent compatible attributes """
        self.cmnd = 'Presence'
        try:
            self.nick = self.fromm.split('/')[1]
        except (AttributeError, IndexError):
            self.nick = ""

        self.jid = self.jid or self.fromm
        self.ruserhost = self.jid
        self.userhost = str(self.jid)
        self.resource = self.nick
        self.stripped = self.jid.split('/')[0]
        self.channel = self.fromm.split('/')[0]
        self.printto = self.channel
        self.origtxt = self.txt
        self.time = time.time()
        
        if self.type == 'groupchat':
            self.groupchat = True
        else:
            self.groupchat = False
