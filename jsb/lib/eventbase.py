# jsb/eventbase.py
#
#

""" base class of all events. """

## jsb imports

from channelbase import ChannelBase
from jsb.utils.lazydict import LazyDict
from jsb.utils.generic import splittxt, stripped, waitforqueue
from errors import NoSuchUser
from jsb.utils.opts import makeeventopts
from jsb.utils.trace import whichmodule
from jsb.utils.locking import lockdec
from jsb.lib.config import Config

## basic imports

from xml.sax.saxutils import unescape
import copy
import logging
import Queue
import types
import socket
import threading
import time
import thread

## defines

cpy = copy.deepcopy
lock = thread.allocate_lock()
locked = lockdec(lock)

## classes

class EventBase(LazyDict):

    """ basic event class. """

    def __init__(self, input={}, bot=None):
        LazyDict.__init__(self)
        if bot: self.bot = bot
        self.bottype = "botbase"
        self.relayed = []
        self.copyin(input)
        
    def __deepcopy__(self, a):
        """ deepcopy an event. """
        logging.debug("eventbase - cpy - %s" % type(self))
        e = EventBase(self)
        return e

    def ready(self, finish=True):
        """ signal the event as ready - push None to all queues. """
        logging.debug("%s - %s - ready called from %s" % (self.cbtype, self.txt, whichmodule()))
        time.sleep(0.01)
        if self.closequeue and self.queues:
            for q in self.queues:
                q.put_nowait(None)
        if not self.dontclose:
            self.outqueue.put_nowait(None)
            self.resqueue.put_nowait(None)
            self.inqueue.put_nowait(None)
        if finish: self.finished.set()

    def prepare(self, bot=None):
        """ prepare the event for dispatch. """
        if bot: self.bot = bot
        assert(self.bot)
        self.origin = self.channel
        self.origtxt = self.txt
        self.makeargs()
        logging.debug("%s - prepared event - %s" % (self.auth, self.cbtype))

    def bind(self, bot=None, user=None, chan=None):
        """ bind event.bot event.user and event.chan to execute a command on it. """
        target = self.auth
        assert target
        bot = bot or self.bot
        assert bot
        if not self.user and target:
            cfg = Config()
            if cfg.auto_register: 
                bot.users.addguest(target)
            self.user = user or bot.users.getuser(target)
            logging.warn("eventbase - binding user - %s - from %s" % (str(self.user), whichmodule()))
        if not self.chan:
            if chan: self.chan = chan
            elif self.channel: self.chan = ChannelBase(self.channel, bot.botname)
            elif self.userhost: self.chan = ChannelBase(self.userhost, bot.botname)
            logging.warn("eventbase - binding channel - %s" % str(self.chan))
        if not self.user: logging.info("eventbase - no %s user found .. setting nodispatch" % target) ; self.nodispatch = True
        self.prepare(bot)
        return self

    def parse(self, event, *args, **kwargs):
        """ overload this. """
        self.bot = event.bot
        self.origin = event.origin
        self.ruserhost = self.origin
        self.userhost = self.origin
        self.channel = event.channel
        self.auth = stripped(self.userhost)

    def waitfor(self, millisec=10000):
        """ wait for the event to finish. """
        logging.warn("eventbase - waiting for %s" % self.txt)
        self.finished.wait(5)
        return waitforqueue(self.resqueue , millisec)

    def copyin(self, eventin):
        """ copy in an event. """
        self.update(eventin)
        self.threads = self.threads or []
        self.queues = self.queues or []
        self.finished = self.finished or threading.Event()
        self.resqueue = self.resqueue or Queue.Queue()
        self.inqueue = self.inqueue or Queue.Queue()
        self.outqueue = self.outqueue or Queue.Queue()
        return self

    @locked
    def reply(self, txt, result=[], event=None, origin="", dot=u", ", nr=375, extend=0, *args, **kwargs):
        """ reply to this event """
        if self.checkqueues(result): return self
        if self.silent:
            self.msg = True
            self.bot.say(self.nick, txt, result, self.userhost, extend=extend, event=self, *args, **kwargs)
        elif self.isdcc: self.bot.say(self.sock, txt, result, self.userhost, extend=extend, event=self, *args, **kwargs)
        else: self.bot.say(self.channel, txt, result, self.userhost, extend=extend, event=self, *args, **kwargs)
        return self

    def missing(self, txt):
        """ display missing arguments. """
        self.reply("%s %s" % (self.usercmnd, txt), event=self) 
        return self

    def done(self):
        """ tell the user we are done. """
        self.reply('<b>done</b> - %s' % self.txt, event=self)
        return self

    def leave(self):
        """ lower the time to leave. """
        self.ttl -= 1
        if self.ttl <= 0 : self.status = "done"
        logging.info("======== STOP handling event ========")

    def makeoptions(self):
        """ check the given txt for options. """
        try: self.options = makeeventopts(self.txt)
        except: return 
        if not self.options: return
        logging.debug("eventbase - options - %s" % unicode(self.options))
        self.txt = ' '.join(self.options.args)
        self.makeargs()

    def makeargs(self):
        """ make arguments and rest attributes from self.txt. """
        if not self.txt:
            self.args = []
            self.rest = ""
        else:
            args = self.txt.split()
            self.chantag = args[0]
            if len(args) > 1:
                self.args = args[1:]
                self.rest = ' '.join(self.args)
            else:
                self.args = []
                self.rest = ""

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
        """ check whether the event is off remote origin. """
        if self.txt: return self.txt.startswith('{"') or self.txt.startswith("{&")

    def iscmnd(self):
        """ check if event is a command. """
        if not self.txt: logging.warn("eventbase - no txt set.") ; return
        if self.iscommand: return self.txt
        if self.isremote(): logging.info("eventbase - event is remote") ; return
        logging.debug("eventbase - trying to match %s" % self.txt)
        cc = "!"
        if not self.chan: self.chan = ChannelBase(self.channel, self.bot.botname) 
        cc = self.chan.data.cc
        if not cc: self.chan.data.cc = "!" ; self.chan.save()
        if not cc: cc = "!"
        if self.type == "DISPATCH": cc += "!"
        if not self.bot: logging.warn("eventbase - bot is not bind into event.") ; return False
        logging.debug("eventbase - cc for %s is %s (%s)" % (self.title or self.channel or self.userhost, cc, self.bot.nick))
        if self.txt[0] in cc: return self.txt[1:]
        matchnick = unicode(self.bot.nick + u":")
        if self.txt.startswith(matchnick): return self.txt[len(matchnick):]
        return False
