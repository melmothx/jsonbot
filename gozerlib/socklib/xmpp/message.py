# gozerlib/socklib/xmpp/message.py
#
#

""" jabber message definition .. types can be normal, chat, groupchat, 
    headline or  error
"""

## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.utils.trace import whichmodule
from gozerlib.utils.generic import toenc, fromenc, jabberstrip
from gozerlib.utils.locking import lockdec
from gozerlib.eventbase import EventBase
from gozerlib.config import cfg
from gozerlib.channelbase import ChannelBase
from gozerlib.errors import BotNotSetInEvent

## xmpp imports

from core import XMLDict

## basic imports

import types
import time
import thread
import logging

## locks
replylock = thread.allocate_lock()
replylocked = lockdec(replylock)

if cfg['dotchars']:
    dotchars = cfg['dotchars']
else:
    dotchars = ' .. '

class Message(XMLDict):

    """ jabber message object. """

    def __init__(self, nodedict={}):
        XMLDict.__init__(self, nodedict)
        self.element = "message"
        self.jabber = True
        self.cmnd = "MESSAGE"
        self.cbtype = "MESSAGE"
        self.bottype = "xmpp"
  
    def __copy__(self):
        return Message(self)

    def __deepcopy__(self, bla):
        return Message(self)

    def reply(self, txt, result=[], to="", dot=", ", extend=0):
        if self.checkqueues(result):
            return
        restxt = self.makeresponse(txt, result, dot)
        res1, res2 = self.less(restxt, 900+extend)
        self.out(res1, to)
        if res2:
            self.out(res2, to)

    def out(self, txt, to=""):
        outtype = self.type

        if not self.bot:
            raise BotNotSetInEvent("xmpp.message")

        if to and to in self.bot.state['joinedchannels']:
            outtype = 'groupchat' 
            self.groupchat = True
            self.msg = False

        repl = Message({'from': self.me, 'to': to or self.jid, 'type': outtype, 'txt': txt})

        if self.groupchat:
            if self.resource == self.bot.nick:
                return
            if to:
                pass
            elif self.printto:
                repl.to = self.printto
            else:
                repl.to = self.channel

        if to:
            repl.type = 'normal'
        elif not repl.type:
            repl.type = 'chat'

        self.bot.send(repl)

    def parse(self, bot=None):
        """ set ircevent compat attributes. """
        self.bot = bot
        self.jidchange = False
        self.cmnd = 'Message'
        try:
            self.resource = self.fromm.split('/')[1]
        except IndexError:
            pass

        self.channel = self['fromm'].split('/')[0]
        self.chan = ChannelBase(self.channel)
        self.origchannel = self.channel
        self.nick = self.resource
        self.jid = self.fromm
        self.ruserhost = self.jid
        self.userhost = self.jid
        self.stripped = self.jid.split('/')[0]
        self.auth = self.stripped
        self.printto = self.channel

        for node in self.subelements:
            try:
                self.txt = node.body.data
            except (AttributeError, ValueError):
                continue

        if self.txt:
            self.usercmnd = self.txt.split()[0]
        else:
            self.usercmnd = ""
        self.origtxt = self.txt
        self.time = time.time()

        if self.type == 'groupchat':
            self.groupchat = True
            if self.jidchange:
                self.userhost = self.stripped
        else:
            self.groupchat = False
            self.userhost = self.stripped

        self.msg = not self.groupchat
        self.makeargs()

    def errorHandler(self):
        """ dispatch errors to their handlers. """
        try:
            code = self.get('error').code
        except Exception, ex:
            handle_exception()
        try:
            method = getattr(self, "handle_%s" % code)
            if method:
                logging.error('sxmpp.core - dispatching error to handler %s' % str(method))
                method(self)
        except AttributeError, ex:
            logging.error('sxmpp.core - unhandled error %s' % code)
        except:
            handle_exception()
