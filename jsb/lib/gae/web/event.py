# jsb/web/event.py
#
#

""" web event. """

## jsb imports

from jsb.lib.eventbase import EventBase
from jsb.utils.generic import splittxt, fromenc, toenc
from jsb.utils.xmpp import stripped
from jsb.lib.outputcache import add
from jsb.utils.url import getpostdata
from jsb.utils.exception import handle_exception
from jsb.lib.channelbase import ChannelBase

## gaelib imports

from jsb.lib.gae.utils.auth import checkuser

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
        self.bot = bot

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
        logging.warn("web - how is %s" % self.how)
        self.webchan = request.get('webchan')
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
        logging.debug(u'web - parsed - %s - %s' % (self.txt, self.userhost)) 
        self.makeargs()
        return self


    def reply(self, txt, result=[], event=None, origin="", dot=u", ", nr=600, extend=0, *args, **kwargs):
        """ reply to this event """#
        if self.checkqueues(result): return
        if not txt: return
        if self.how == "background":
            txt = self.bot.makeoutput(self.channel, txt, result, origin=origin, nr=nr, extend=extend, *args, **kwargs)
            self.bot.outnocb(self.channel, txt, self.how, response=self.response)
        else:
            self.bot.say(self.channel, txt, result, self.how)
        #self.result.append(txt)
        #self.outqueue.put_nowait(txt)
        return self
