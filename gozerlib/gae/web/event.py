# gozerlib/web/event.py
#
#

""" web event. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.utils.generic import splittxt
from gozerlib.utils.xmpp import stripped

## gaelib imports

from gozerlib.gae.utils.auth import checkuser
from gozerlib.gae.wave.waves import Wave

## basic imports

import cgi
import logging

class WebEvent(EventBase):

    def __init__(self): 
        EventBase.__init__(self)
        self.type = "web"

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

        if len(input) > 1 and input[0] in '!?' :
            input = input[1:]

        self.txt = input
        self.usercmnd = self.txt and self.txt.split()[0]
        self.groupchat = False
        self.response = response
        self.request = request
        (userhost, user, u, nick) = checkuser(response, request)
        self.user = user
        self.userhost = userhost
        self.nick = nick
        self.auth = userhost
        self.stripped = stripped(userhost)
        self.domain = None
        self.waveid = request.get('waveid')

        if self.waveid:
            self.isgadget = True
            wave = Wave(self.waveid)
            
            if wave:
                logging.warn('web - setting channel to %s - %s' % (self.waveid, wave.data.title))
            else:
                logging.warn('web - setting channel to %s' % self.waveid)

        if self.waveid:
            self.channel = self.waveid
            self.domain = self.waveid.split('!')[0]
        else:
            self.channel = stripped(userhost)

        self.makeargs()
        logging.warn(u'web - in - %s - %s' % (self.userhost, self.txt)) 
        return self

    def _raw(self, txt, end=""):

        """ 
            put txt onto the reponse object .. adding end string if provided. 
            output is NOT escaped.

        """

        txt = unicode(txt)
        logging.info(u'web - out - %s - %s' % (self.userhost, txt))
        self.response.out.write(txt + end)
        self.bot.outmonitor(self.userhost, self.channel, txt, self)

    def write(self, txt, start=u"", end=u"<br><br>", raw=False):

        """ 
            put txt onto the reponse object .. adding end string if provided. 
            output IS escaped.

        """
         
        if not raw:
            self._raw(start + cgi.escape(txt) + end)
        else:
            self._raw(start + txt + end)

    def makeresponse(self, txt, resultlist, nritems, dot, *args, **kwargs):
        if dot == "\n":
            dot = "<br>"
        return EventBase.makeresponse(self, txt, resultlist, nritems, dot, *args, **kwargs)

    def reply(self, txt, resultlist=[], nritems=False, dot=", ", raw=False, *args, **kwargs):

        """ send reply to the web user. """

        if self.checkqueues(resultlist):
            return

        result = self.makeresponse(txt, resultlist, nritems, dot, *args, **kwargs)
        (res1, res2) = self.less(result)
        self.write(res1, raw=raw)
        if res2:
            self.write(res2, raw=raw)
