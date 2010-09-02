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
from gozerlib.gozerevent import GozerEvent

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

## classes

class Message(GozerEvent):

    """ jabber message object. """

    def __init__(self, nodedict={}):
        self.element = "message"
        self.jabber = True
        self.cmnd = "MESSAGE"
        self.cbtype = "MESSAGE"
        self.bottype = "xmpp"
        self.type = "normal"
        GozerEvent.__init__(self, nodedict)
  
    def __copy__(self):
        return Message(self)

    def __deepcopy__(self, bla):
        m = Message()
        m.copyin(self)
        return m

    def reply(self, txt, result=[], to="", dot=", ", extend=0, raw=False):
        if self.checkqueues(result):
            return
        restxt = self.makeresponse(txt, result, dot)
        res1, res2 = self.less(restxt, 900+extend)
        self.out(res1, to)
        self.bot.outmonitor(self.userhost, to or self.channel, res1, self)

    def out(self, txt, to=""):
        outtype = self.type

        if not self.bot:
            raise BotNotSetInEvent("xmpp.message")

        if to  and to in self.bot.state['joinedchannels']:
            outtype = 'groupchat' 
            self.groupchat = True
            self.msg = False

        if self.type == "groupchat":
            target = to or self.channel
            self.groupchat = True
        else:
            target = to or self.userhost

        repl = Message({'from': self.me, 'to': target, 'type': self.type, 'txt': txt})

        if not repl.type:
            repl.type = 'chat'

        logging.debug("sxmpp - target is %s - %s" % (target, self.type))

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
        self.origchannel = self.channel
        self.nick = self.resource
        self.jid = self.fromm
        self.ruserhost = self.jid
        self.userhost = self.jid
        self.stripped = self.jid.split('/')[0]
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
            self.auth = self.userhost
        else:
            self.groupchat = False
            self.auth = self.stripped
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
