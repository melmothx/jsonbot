# gozerlib/web/event.py
#
#

""" web event. """

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.utils.generic import splittxt, fromenc, toenc
from gozerlib.utils.xmpp import stripped
from gozerlib.outputcache import add
from gozerlib.utils.url import getpostdata
from gozerlib.utils.exception import handle_exception
from gozerlib.channelbase import ChannelBase

## gaelib imports

from gozerlib.gae.utils.auth import checkuser

## basic imports

import cgi
import logging
import re

## WebEvent class

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
        how = request.get('how')
        if not how:
            try: how = request.params.getone('how')
            except KeyError: how = "normal"
            except Exception, ex:
                how = "normal"
                handle_exception()
        if not how:
            try: how = request.GET['how']
            except KeyError: pass
        self.how = how
        if self.how == "undefined": self.how = "normal"
        input = request.get('content') or request.get('cmnd')
        if not input:
            try: input = request.params.getone('content') or request.params.getone('cmnd')
            except KeyError: input = ""
            except Exception, ex:
                input = ""
                handle_exception()
            if not input:
                try: input = request.GET['content'] or request.GET['cmnd']
                except KeyError: pass
        self.isweb = True
        self.origtxt = fromenc(input.strip(), self.bot.encoding)
        self.txt = self.origtxt
        self.usercmnd = self.txt and self.txt.split()[0]
        self.groupchat = False
        self.response = response
        self.request = request
        (userhost, user, u, nick) = checkuser(response, request, self)
        self.userhost = fromenc(userhost)
        self.nick = fromenc(nick)
        self.auth = fromenc(userhost)
        self.stripped = stripped(self.auth)
        self.domain = None
        self.channel = stripped(userhost)
        logging.info(u'web - parsed - %s - %s' % (self.txt, self.userhost)) 
        self.makeargs()
        return self


    def reply(self, txt, result=[], event=None, origin="", dot=u", ", nr=600, extend=0, *args, **kwargs):
        """ reply to this event """#
        if self.checkqueues(result): return
        txt = self.bot.makeoutput(self.channel, txt, result, origin=origin, nr=nr, extend=extend, *args, **kwargs)
        if not txt: return
        if self.how == "background": self.bot.outnocb(self.channel, txt, response=self.response)
        else: self.bot.out(self.channel, txt, response=self.response)
        self.result.append(txt)
        self.outqueue.put_nowait(txt)
        return self
