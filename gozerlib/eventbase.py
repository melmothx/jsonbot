# gozerlib/eventbase.py
#
#

""" base class of all events. """

## gozerlib imports

from channelbase import ChannelBase
from utils.lazydict import LazyDict
from utils.generic import splittxt, stripped
from errors import NoSuchUser
from config import cfg as mainconfig

## simplejson imports

from simplejson import dumps, loads

## basic imports

from  xml.sax.saxutils import unescape
import copy
import logging
import Queue
import types
import socket

## defines

cpy = copy.deepcopy

## classes

class EventBase(LazyDict):

    """ basic event class. """

    def __init__(self, input=None, bot=None):
        """ EventBase constructor """
        LazyDict.__init__(self)
        if bot: self.bot = bot
        if input: self.copyin(input)
        self.result = []
        self.inqueue = Queue.Queue()
        self.outqueue = Queue.Queue()
        self.bottype = "botbase"
        self.closequeue = True
        self.printto = self.channel
        self.ttl = 1
        self.how = "normal"

    def __deepcopy__(self, a):
        """ deepcopy an event. """
        e = EventBase()
        e.copyin(self)
        return e

    def prepare(self, bot=None):
        self.result = []
        if bot: self.bot = bot
        assert(self.bot)
        self.origin = self.bot.user or self.bot.server
        self.origtxt = self.txt
        self.makeargs()
        logging.debug("%s - prepared event - %s" % (self.auth, self.dump()))

    def finish(self, bot=None):
        """ finish a event to execute a command on it. """
        target = self.auth
        if not self.user and target:
            if mainconfig.auto_register: self.bot.users.addguest(target)
            self.user = self.bot.users.getuser(target)
        if not self.chan:
            if self.channel: self.chan = ChannelBase(self.channel)
            elif self.userhost: self.chan = ChannelBase(self.userhost)
        if not self.user: self.nodispatch = True
        self.prepare()
        if self.txt: self.usercmnd = self.txt.split()[0]
        logging.debug("%s - finish - %s" % (self.auth, self.dump()))

    def _raw(self, txt):
        """ put rawstring to the server .. overload this """
        pass

    def parse(self, event, *args, **kwargs):
        """ overload this. """
        self.bot = event.bot
        self.origin = event.origin
        self.ruserhost = self.origin
        self.userhost = self.origin
        self.channel = event.channel
        self.auth = stripped(self.userhost)

    def copyin(self, eventin):
        """ copy in an event. """
        if not eventin:
            logging.error("no event given in copyin")
            return self
        self.update(eventin)
        if eventin.has_key("sock"): self.sock = eventin['sock']
        if eventin.has_key("chan") and eventin['chan']: self.chan = eventin['chan']
        if eventin.has_key("user"): self.user = eventin['user']
        if eventin.has_key('queues'):
            if eventin['queues']: self.queues = eventin['queues']
        if eventin.has_key("outqueue"): self.inqueue = eventin['outqueue']
        return self

    #def writenocb(self, txt, result=[], event=None, origin="", dot=u", ", extend=0, *args, **kwargs):
    #    if self.checkqueues(result): return
    #    self.bot.writenocb(self.channel, txt, result)
    #    self.result.append(txt)
    #    self.outqueue.put_nowait(txt)

    #def write(self, txt, result=[], event=None, origin="", dot=u", ", nr=375, extend=0, *args, **kwargs):
    #    self.writenocb(txt, result, event, origin, dot, nr, extend, *args, **kwargs)
    #    self.outqueue.put_nowait(txt)

    def reply(self, txt, result=[], event=None, origin="", dot=u", ", nr=375, extend=0, *args, **kwargs):
        """ reply to this event """
        if self.checkqueues(result): return
        self.bot.say(self.channel, txt, result, origin=origin or self.userhost, extend=extend, *args, **kwargs)
        self.result.append(txt)
        self.outqueue.put_nowait(txt)
        return self

    def missing(self, txt):
        """ display missing arguments. """
        self.reply("%s %s" % (self.usercmnd, txt)) 
        return self

    def done(self):
        """ tell the user we are done. """
        self.reply('<b>done</b> - %s' % self.txt)
        return self

    def leave(self):
        self.ttl -= 1
        if self.ttl <= 0 : self.status = "done"

    def makeargs(self):
        """ make arguments and rest attributes from self.txt. """
        args = self.txt.split()
        if len(args) > 1:
            self.args = args[1:]
            self.rest = ' '.join(self.args)
          
    def checkqueues(self, resultlist):
        """ check if resultlist is to be sent to the queues. if so do it. """
        if self.queues:
            for queue in self.queues:   
                for item in resultlist:
                    if item: queue.put_nowait(item)
            for item in resultlist:
                if item: self.outqueue.put_nowait(item)      
            return True
        return False

    def makeresponse(self, txt, result, dot=u", ", *args, **kwargs):
        """ create a response from a string and result list. """
        return self.bot.makeresponse(txt, result, dot, *args, **kwargs)

    def less(self, what, nr=365):
        """ split up in parts of <nr> chars overflowing on word boundaries. """
        return self.bot.less(what, nr)

    def isremote(self):
        if self.txt: return self.txt.startswith('{"')

    def iscmnd(self):
        """ check if event is a command. """
        if self.txt and self.txt.startswith('{"'): return # isremote
        cc = "!"
        if self.chan: 
            cc = self.chan.data.cc
            if not cc:
                self.chan.data.cc = "!"
                self.chan.save()
        if not cc: cc = "!"
        if self.type == "DISPATCH": cc += "!"
        logging.debug("dispatch - cc for %s is %s (%s)" % (self.title or self.channel or event.userhost, cc, self.bot.nick))
        matchnick = unicode(self.bot.nick + u":")
        logging.warn("dispatch - trying to match %s" % self.txt)
        if self.txt and self.txt[0] in cc: return self.txt[1:]
        elif self.txt.startswith(matchnick): return self.txt[len(matchnick):]
        return False

    def normalize(self, txt):
        """ allow certain html markup. """
        txt = txt.replace("&lt;br&gt;", "<br>")
        txt = txt.replace("&lt;i&gt;", "<i>")
        txt = txt.replace("&lt;/i&gt;", "</i>")
        txt = txt.replace("&lt;b&gt;", "<b>")
        txt = txt.replace("&lt;/b&gt;", "</b>")
        txt = txt.replace("&lt;h2&gt;", "<h2>")
        txt = txt.replace("&lt;/h2&gt;", "</h2>")
        txt = txt.replace("&lt;h3&gt;", "<h3>")
        txt = txt.replace("&lt;/h3&gt;", "</h3>")
        txt = txt.replace("&lt;li&gt;", "<li>")
        txt = txt.replace("&lt;/li&gt;", "</li>")
        txt = txt.replace("\n", "<br>")
        return txt
