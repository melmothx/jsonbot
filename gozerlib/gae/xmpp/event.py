# gaelib/xmpp/event.py
#
#

""" an xmpp event. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.utils.xmpp import stripped, resource
from gozerlib.utils.lazydict import LazyDict

## gaelibs imports

from gozerlib.gae.utils.auth import checkuser

## google imports

from google.appengine.api import xmpp

## basic imports

import cgi
import logging

class XMPPEvent(EventBase):

    """ an XMPP event. """

    def __init__(self): 
        EventBase.__init__(self)
        self.type = "xmpp"
        self.cbtype = 'MESSAGE'

    def __deepcopy__(self, a):

        """ make a deepcopy of this XMPPEvent. """

        return XMPPEvent().copyin(self)

    def _raw(self, txt):

        """ output data to user. txt is NOT escaped. """

        txt = unicode(txt)
        logging.warn(u"xmpp - out - %s - %s" (self.userhost, txt))

        if txt:
            xmpp.send_message([self.userhost, ], txt)
            self.bot.outmonitor(self.origin, self.userhost, txt, self)

    def parse(self, request, response):

        """ parse incoming request/response into a XMPPEvent. """

        self.copyin(LazyDict(request.POST))
        (userhost, user, u, nick) = checkuser(response, request)
        self.userhost = stripped(self['from'])
        self.origin = self.channel

        if user:
            self.auth = user.email()
        else:
            self.auth = self.userhost

        logging.warn('xmpp - auth is %s' % self.auth)
        self.resource = resource(self['from'])
        self.jid = self['from']
        self.to = stripped(self['to'])
        self.channel = self.userhost
        self.origin = self.channel
        input = self.body
        self.origtxt = input

        if len(input) > 1 and input[0] == '!':
            input = input[1:]
            
        self.txt = input
        self.usercmnd = self.txt.split()[0]
        self.makeargs()
        logging.warn(u'xmpp - in - %s - %s' % (self.userhost, self.txt))
        return self

    def reply(self, txt, resultlist=[], nritems=False, dot="\n", *args, **kwargs):

        """ reply with txt and optional resultlist. result lists can be 
            passed on onto the events queues. 
        """

        if self.checkqueues(resultlist):
            return

        result = self.makeresponse(txt, resultlist, nritems, dot, *args, **kwargs)

        (res1, res2) = self.less(result)
        self.write(res1)

        if res2:
            self.write(res2)

    def write(self, txt):

        """ output txt to the user .. output IS escaped. """

        if txt:
            txt = unicode(txt)
            logging.warn(u"xmpp - out - %s - %s" % (self.userhost, txt))
            xmpp.send_message([self.userhost, ], cgi.escape(txt))
            self.bot.outmonitor(self.origin, self.userhost, txt, self)
