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

    def __init__(self, input=None):
        """ EventBase constructor """
        LazyDict.__init__(self)
        if input:
            self.copyin(input)
        self.result = []
        self.outqueue = Queue.Queue()
        self.bottype = "console"

    def __deepcopy__(self, a):
        """ deepcopy an event. """
        e = EventBase()
        e.copyin(self)
        return e

    def _raw(self, txt):
        """ put rawstring to the server .. overload this """
        pass

    def parse(self, *args, **kwargs):
        """ overload this. """
        pass

    def copyin(self, eventin):
        """ copy in an event. """
        if not eventin:
            logging.error("no event given in copyin")
            return self
        self.update(eventin)
        if eventin.has_key('queues'):
            if eventin['queues']:
                self.queues = list(eventin['queues'])

        return self

    def reply(self, txt, result=[], event=None, origin="", dot=u", ", extend=0, *args, **kwargs):
        """ reply to this event """
        if self.checkqueues(result):
            return

        txt = self.makeresponse(txt, result, dot)

        res1, res2 = self.less(txt, 1000)
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
                    queue.put_nowait(item)

            return True
        return False

    def makeresponse(self, txt, result, dot=u", ", *args, **kwargs):
        """ create a response from a string and result list. """
        res = []
        # check if there are list in list
        for i in result:
            if type(i) == types.ListType or type(i) == types.TupleType:
                try:
                    res.append(dotchars.join(i))
                except TypeError:
                    res.extend(unicode(i))
            else:
                res.append(unicode(i))


        if txt:
            return txt + dot.join(res)
        elif result:
            return dot.join(res)
        return ""
            
    def less(self, what, nr=365):
        """ check string for overflow, if so send data to the output cache. """
        return self.bot.less(self.userhost, what, nr)
