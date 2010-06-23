# gozerlib/web/event.py
#
#

""" web event. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.utils.generic import splittxt, fromenc
from gozerlib.utils.xmpp import stripped
from gozerlib.outputcache import add

## gaelib imports

from gozerlib.gae.utils.auth import checkuser
from gozerlib.gae.wave.waves import Wave

## basic imports

import cgi
import logging

class WebEvent(EventBase):

    def __init__(self, bot=None): 
        EventBase.__init__(self, bot=bot)
        self.bottype = "web"

    def __deepcopy__(self, a):
        e = WebEvent()
        e.copyin(self)
        return e

    def parse(self, response, request):
        """ parse request/response into a WebEvent. """
        #logging.warn('%s %s' % (dir(request), dir(response)))
        #logging.warn(str(request.environ))
        input = request.get('content')
        if not input:
            input = request.get('QUERY_STRING')
        self.isweb = True
        self.origtxt = input.strip()
        self.txt = fromenc(input)
        self.usercmnd = self.txt and self.txt.split()[0]
        self.groupchat = False
        self.response = response
        self.request = request
        (userhost, user, u, nick) = checkuser(response, request, self)
        self.user = user
        self.userhost = userhost
        self.nick = nick
        self.auth = userhost
        self.stripped = stripped(userhost)
        self.domain = None
        self.waveid = request.get('waveid')

        if self.waveid:
            self.channel = self.waveid
            self.domain = self.waveid.split('!')[0]
        else:
            self.channel = stripped(userhost)

        if self.waveid:
            self.isgadget = True
            logging.debug('web - setting channel to %s' % self.waveid)
            self.channel = self.waveid

        self.chan = Wave(self.channel)
        self.makeargs()
        logging.debug(u'web - in - %s - %s' % (self.userhost, self.txt)) 
        return self

    def _raw(self, txt, end=u""):
        """ 
            put txt onto the reponse object .. adding end string if provided. 
            output is NOT escaped.

        """
        logging.debug('web - out - %s - %s' % (self.userhost, str(txt)))
        self.response.out.write(txt + end)
        self.bot.outmonitor(self.userhost, self.channel, txt, self)

    def write(self, txt, start=u"", end=u"<br>", raw=False):
        """ 
            put txt onto the reponse object .. adding end string if provided. 
            output IS escaped.

        """
        if not raw:
            self._raw(start + cgi.escape(txt) + end)
        else:
            self._raw(start + txt + end)

    def reply(self, txt, resultlist=[], event=None, origin=u"", dot=u", ", raw=False, *args, **kwargs):
        """ send reply to the web user. """
        if self.checkqueues(resultlist):
            return

        result = self.makeresponse(txt, resultlist, dot, *args, **kwargs)
        (res1, res2) = self.less(result)
        self.write(res1, raw=raw)
        if res2:
            self.write(res2, raw=raw)
