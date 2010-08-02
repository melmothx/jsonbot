# gozerlib/eventbase.py
#
#

""" base class of all events. """

## imports
from channelbase import ChannelBase
from utils.lazydict import LazyDict
from utils.generic import splittxt

## simplejson imports

from simplejson import dumps, loads

## basic imports

from  xml.sax.saxutils import unescape
import copy
import logging
import Queue
import types

## defines

cpy = copy.deepcopy

## classes

class EventBase(LazyDict):

    """ basic event class. """

    def __init__(self, input=None, bot=None):
        """ EventBase constructor """
        LazyDict.__init__(self)
        if bot:
            self.bot = bot
        if input:
            self.copyin(input)
        self.result = []
        self.outqueue = Queue.Queue()
        self.bottype = "botbase"
        self.closequeue = True
        self.printto = self.channel
        self.origin = self.userhost
        self.isremote = False
        self.iscmnd = False
        self.ttl = 1

    def __deepcopy__(self, a):
        """ deepcopy an event. """
        e = EventBase()
        e.copyin(self)
        return e

    def finish(self):
        self.user = self.bot.users.getuser(self.auth or self.userhost)
        self.makeargs()
        logging.info(" ==> EVENT - %s - %s - %s - %s" % (self.type, self.cbtype, self.usercmnd, self.userhost))

    def _raw(self, txt):
        """ put rawstring to the server .. overload this """
        pass

    def parse(self, event, *args, **kwargs):
        """ overload this. """
        self.bot = event.bot
        self.origin = event.origin
        self.ruserhost = self.origin
        self.auth = self.origin
        self.userhost = self.origin
        self.channel = event.channel
        self.chan = ChannelBase(self.channel)

    def copyin(self, eventin):
        """ copy in an event. """
        if not eventin:
            logging.error("no event given in copyin")
            return self
        self.update(eventin)
        if eventin.has_key("sock"):
            self.sock = eventin['sock']
        
        if eventin.has_key('queues'):
            if eventin['queues']:
                self.queues = list(eventin['queues'])
        return self

    def reply(self, txt, result=[], event=None, origin="", dot=u", ", extend=0, *args, **kwargs):
        """ reply to this event """

        if self.checkqueues(result):
            return
        txt = self.makeresponse(txt, result, dot)
        if self.isdcc:
            self.sock.send(unicode(txt) + u"\n")
            return
        res1, res2 = self.less(txt, 1000+extend)
        self.bot.say(self.channel, res1, origin=origin or self.userhost, extend=extend, *args, **kwargs)

        if res2:
            self.bot.say(self.channel, res2, origin=origin or self.userhost, extend=extend, *args, **kwargs)

        self.result.append(txt)
        self.outqueue.put_nowait(txt)
        return self

    def missing(self, txt):
        """ display missing arguments. """
        self.reply("%s %s" % (self.usercmnd, txt)) 
        return self

    def done(self):
        """ tell the user we are done. """
        self.reply('done')
        return self

    def leave(self):
        self.ttl -= 1
        if self.ttl <= 0 :
            self.status = "done"

    def makeargs(self):
        """ make arguments and rest attributes from self.txt. """
        try:
            self.args = self.txt.split()[1:]
            self.rest = ' '.join(self.args)
        except:
            self.args = None
          
    def checkqueues(self, resultlist):
        """ check if resultlist is to be sent to the queues. if so do it. """
        if self.queues:
            for queue in self.queues:   
                for item in resultlist:
                    if item:
                        queue.put_nowait(item)
            for item in resultlist:
                if item:
                    self.outqueue.put_nowait(item)      
            return True
        return False

    def makeresponse(self, txt, result, dot=u", ", *args, **kwargs):
        """ create a response from a string and result list. """
        return self.bot.makeresponse(txt, result, dot, *args, **kwargs)
            
    def less(self, what, nr=365):
        """ check string for overflow, if so send data to the output cache. """
        return self.bot.less(self.userhost, what, nr)
