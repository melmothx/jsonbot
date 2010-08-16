# gaelib/xmpp/event.py
#
#

""" an xmpp event. """

## gozerlib imports

from gozerlib.channelbase import ChannelBase
from gozerlib.eventbase import EventBase
from gozerlib.utils.xmpp import stripped, resource
from gozerlib.utils.lazydict import LazyDict
from gozerlib.gae.utils.auth import checkuser

## basic imports

import cgi
import logging
import re

## classes

class XMPPEvent(EventBase):

    """ an XMPP event. """

    def __init__(self): 
        EventBase.__init__(self)
        self.bottype = "xmpp"
        self.cbtype = 'MESSAGE'

    def __deepcopy__(self, a):

        """ make a deepcopy of this XMPPEvent. """

        return XMPPEvent().copyin(self)

    def normalize(self, what):
        #what = re.sub("\s+", " ", what)
        what = what.replace("<b>", "")
        what = what.replace("</b>", "")
        what = what.replace("&lt;b&gt;", "")
        what = what.replace("&lt;/b&gt;", "")
        return what

    def _raw(self, txt):

        """ output data to user. txt is NOT escaped. """

        txt = self.normalize(txt)
        txt = unicode(txt)
        logging.debug(u"xmpp - out - %s - %s" (self.userhost, txt))

        if txt:
            from google.appengine.api import xmpp
            xmpp.send_message([self.userhost, ], txt)
            self.bot.outmonitor(self.origin, self.channel, txt, self)

    def parse(self, request, response):

        """ parse incoming request/response into a XMPPEvent. """

        self.copyin(LazyDict(request.POST))
        (userhost, user, u, nick) = checkuser(response, request)
        self.userhost = self['from']
        self.origin = self.channel

        if user:
            self.auth = user.email()
        else:
            self.auth = stripped(self.userhost)

        logging.info('xmpp - auth is %s' % self.auth)
        self.resource = resource(self['from'])
        self.jid = self['from']
        self.to = stripped(self['to'])
        self.channel = stripped(self.userhost)
        self.stripped = stripped(self.userhost)
        self.chan = ChannelBase(self.channel)
        self.origin = self.channel
        input = self.body or self.stanza
        input = input.strip()
        self.origtxt = input
        self.txt = input
        self.usercmnd = self.txt.split()[0].lower()
        self.makeargs()
        logging.debug(u'xmpp - in - %s - %s' % (self.userhost, self.txt))
        return self

    def reply(self, txt, resultlist=[], event=None, origin="", dot=", ", extend=0, raw=True, *args, **kwargs):

        """ reply with txt and optional resultlist. result lists can be 
            passed on onto the events queues. 
        """

        if self.checkqueues(resultlist):
            return

        result = self.makeresponse(txt, resultlist, dot, *args, **kwargs)

        (res1, res2) = self.less(result, 1000+extend)
        self.write(res1, raw)

        if res2:
            self.write(res2, raw)

    def write(self, txt, raw=False):

        """ output txt to the user .. output IS escaped. """

        if txt:
            from google.appengine.api import xmpp
            txt = unicode(cgi.escape(unciode(txt)))
            txt = self.normalize(txt)
            logging.debug(u"xmpp - out - %s - %s" % (self.userhost, txt))
            if not raw:
                xmpp.send_message([self.userhost, ], cgi.escape(txt))
            else:
                xmpp.send_message([self.userhost, ], txt)
            self.bot.outmonitor(self.origin, self.channel, txt, self)
