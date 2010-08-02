# gozerlib/web/event.py
#
#

""" web event. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.utils.generic import splittxt, fromenc, toenc
from gozerlib.utils.xmpp import stripped
from gozerlib.outputcache import add
from gozerlib.utils.url import getpostdata, re_url_match
from gozerlib.utils.exception import handle_exception

## gaelib imports

from gozerlib.gae.utils.auth import checkuser
from gozerlib.gae.wave.waves import Wave

## basic imports

import cgi
import logging
import re

## classes


class WebEvent(EventBase):

    def __init__(self, bot=None): 
        EventBase.__init__(self, bot=bot)
        self.bottype = "web"
        self.cbtype = "WEB"

    def __deepcopy__(self, a):
        e = WebEvent()
        e.copyin(self)
        return e

    def parse(self, response, request):
        """ parse request/response into a WebEvent. """
        #logging.warn('%s %s' % (dir(request), dir(response)))
        #logging.warn(str(request.environ))
        input = request.get('content') or request.get('cmnd')
        if not input:
            try:
                input = request.params.getone('content') or request.params.getone('cmnd')
            except KeyError:
                input = ""
            except Exception, ex:
                input = ""
                handle_exception()
            if not input:
                try:
                    input = request.GET['content'] or request.GET['cmnd']
                except KeyError:
                    pass
        #logging.warn(dir(request))
        logging.warn("web - input is %s" % input)
        self.isweb = True
        self.origtxt = fromenc(input.strip())
        self.txt = self.origtxt
        self.usercmnd = self.txt and self.txt.split()[0]
        self.groupchat = False
        self.response = response
        self.request = request
        (userhost, user, u, nick) = checkuser(response, request, self)
        self.user = user
        self.userhost = fromenc(userhost)
        self.nick = fromenc(nick)
        self.auth = fromenc(userhost)
        self.stripped = stripped(self.auth)
        self.domain = None
        self.waveid = fromenc(request.get('waveid'))

        if self.waveid:
            self.channel = self.waveid
            self.domain = self.waveid.split('!')[0]
        else:
            self.channel = stripped(userhost)

        if self.waveid:
            self.isgadget = True
            logging.debug(u'web - setting channel to %s' % unicode(self.waveid))
            self.channel = self.waveid

        self.chan = Wave(self.channel)
        self.makeargs()
        #logging.debug(u'web - in - %s - %s' % (self.userhost, self.txt)) 
        return self

    def _raw(self, txt, end=u""):
        """ 
            put txt onto the reponse object .. adding end string if provided. 
            output is NOT escaped.

        """
        #logging.debug(u'web - out - %s - %s' % (self.userhost, str(txt)))
        self.response.out.write(txt + end)
        self.bot.outmonitor(self.userhost, self.channel, txt, self)

    def write(self, txt, start=u"", end=u"<br>", raw=False):
        """ 
            put txt onto the reponse object .. adding end string if provided. 
            output IS escaped.

        """
        if not raw:
            txt = cgi.escape(txt)
        if "http://" in txt:
            for item in re_url_match.findall(txt):
                 logging.debug("web - raw - found url - %s" % item)
                 txt = re.sub(item, '<a href="%s" onclick="window.open(\'%s\'); return false;">%s</a>' % (item, item, item), txt)
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
