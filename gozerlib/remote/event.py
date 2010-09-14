# gozerlib/remote/event.py
#
#

""" gozerlib remote event. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.utils.generic import splittxt
from gozerlib.utils.lazydict import LazyDict
from gozerlib.container import Container
from gozerlib.gozerevent import GozerEvent

## simplejson imports

from simplejson import loads

## basic imports

import cgi
import logging
import copy
import time

## defines

cpy = copy.deepcopy

## classes

class RemoteEvent(GozerEvent):

    def __init__(self): 
        GozerEvent.__init__(self)
        self.type = "remote"

    def __deepcopy__(self, a):
        e = RemoteEvent()
        e.copyin(self)
        return e

    def parse(self, response, request):

        """ parse request/response into a RemoteEvent. """

        logging.warn(u'%s %s' % (dir(request), dir(response)))
        logging.warn(str(request))
        eventin = request.get('container')
        if not eventin: 
            eventin = request.environ.get('QUERY_STRING')
            if not eventin:
                return ["can't determine eventin", ]
        origin = request.get('origin')
        if not origin:
            origin = str(request.remote_addr)
        #logging.info(eventin)
        logging.warn(u"remote.event - %s - parsing %s" % (origin, unicode(eventin)))
        container = Container()
        container.load(event.txt)
        self.load(container.payload)
        self.prepare()
        self.isremote = True
        self.response = response
        self.request = request
        self.remoteout = origin
        logging.info(u'remote.event - in - %s - %s' % (self.userhost, self.txt)) 
        return self

    def _raw(self, txt, end=""):

        """ 
            put txt onto the reponse object .. adding end string if provided. 
            output is NOT escaped.

        """

        txt = unicode(txt)
        logging.info(u'remove.event - out - %s - %s' % (self.userhost, txt))
        self.bot.say(self.remoteout, txt, self)

    def write(self, txt, start=u"", end=u"<br>", raw=False):

        """ 
            put txt onto the reponse object .. adding end string if provided. 
            output IS escaped.

        """
         
        if not raw:
            self._raw(start + cgi.escape(txt) + end)
        else:
            self._raw(start + txt + end)

    def reply(self, txt, resultlist=[], nritems=False, dot=" .. ", raw=False, *args, **kwargs):

        """ send reply to the web user. """

        if self.checkqueues(resultlist):
            return

        result = self.makeresponse(txt, resultlist, nritems, dot, *args, **kwargs)
        self.write(result)
