# gozerlib/eventbase.py
#
#

""" base class of all events. """

## imports

from utils.lazydict import LazyDict
from utils.generic import splittxt

## simplejson imports

from simplejson import dumps, loads

## basic imports

from  xml.sax.saxutils import unescape
import copy
import logging

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

    def __deepcopy__(self, a):
        """ deepcopy an event. """
        e = EventBase()
        e.copyin(self)
        return e

    def _raw(self, txt):
        """ put rawstring to the server .. overload this """
        logging.info(u"eventbase - out - %s - %s" % (self.userhost, unicode(txt)))
        print u"> " + txt
        self.result.append(txt)

    def parse(self, *args, **kwargs):
        """ overload this. """
        pass

    def copyin(self, eventin):
        """ copy in an event. """
        self.update(eventin)
        if eventin.has_key('queues'):
            self.queues = list(eventin['queues'])
        #if eventin.inqueue:
        #    self.inqueue = cpy(eventin.inqueue)

        return self

    def reply(self, txt, result=[], *args, **kwargs):
        """ reply to this event """
        if self.checkqueues(result):
            return

        resp = self.makeresponse(txt, result, *args, **kwargs)

        if self.bot:
            self.bot.say(self.channel, resp)
        else:
            self._raw(resp)

        self.result.append(resp)
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

    def makeresponse(self, txt, result, nritems=False, dot=", ", *args, **kwargs):
        if txt:
            return txt + dot.join(result)
        elif result:
            return dot.join(result)
        return ""
            
    def less(self, what):
        what = what.strip()
        txtlist = splittxt(what, 1000)
        size = 0

        # send first block
        res = txtlist[0]

        # see if we need to store output in less cache
        result = ""
        if len(txtlist) > 2:
            logging.warn("addding %s lines to %s outputcache" % (len(txtlist), self.userhost))
            self.bot.outcache.add(self.userhost, txtlist[1:])
            size = len(txtlist) - 2
            result = txtlist[1:2][0]
            if size:
                result += " (+%s)" % size
        else:
            if len(txtlist) == 2:
                result = txtlist[1]

        return [res, result] 
