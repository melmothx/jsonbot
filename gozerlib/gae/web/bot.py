# gozerlib/gae/web/bot.py
#
#

""" GAE web bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.outputcache import add
from gozerlib.utils.generic import toenc, fromenc, strippedtxt
from gozerlib.utils.url import re_url_match
from gozerlib.channelbase import ChannelBase

## basic imports

import logging
import re
import cgi
import urllib

## WebBot class

class WebBot(BotBase):

    """ webbot just inherits from botbase for now. """

    def __init__(self, cfg=None, users=None, plugs=None, botname="gae-web", *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, botname, *args, **kwargs)
        if self.cfg: self.cfg['type'] = u'web'
        self.isgae = True
        self.type = u"web"

    def _raw(self, txt, response=None, end=u"<br>", chan=None):
        """  put txt to the client. """
        if not txt or not response: return 
        logging.debug("%s - web - out - %s" % (self.name, txt))
        if chan:
            from google.appengine.api import channel
            #chan = ChannelBase(chan, botname=self.name)
            #logging.warn("%s - using token %s" % (self.name, chan.data.token))
            channel.send_message(chan, txt)
        else:
            response.out.write(toenc(txt + end))

    def outnocb(self, channel, txt, how="msg", event=None, origin=None, response=None, *args, **kwargs):
        txt = self.normalize(txt)
        if event and not event.how == "background": logging.warn("%s - out - %s" % (self.name, txt))             
        #if not response or how == 'cache': add(channel, [txt, ])
        if True:
            if "http://" in txt:
                 for item in re_url_match.findall(txt):
                     logging.debug("web - raw - found url - %s" % item)
                     url = u'<a href="%s" onclick="window.open(\'%s\'); return false;"><b>%s</b></a>' % (item, item, item)
                     try: txt = re.sub(item, url, txt)
                     except ValueError:  logging.error("web - invalid url - %s" % url)
            self._raw(txt, response, chan=channel)

    def normalize(self, txt):
        #txt = cgi.escape(txt)
        txt = txt.replace("&lt;br&gt;", "<br>")
        txt = txt.replace("&lt;b&gt;", "<b>")
        txt = txt.replace("&lt;/b&gt;", "</b>")
        txt = txt.replace("&lt;i&gt;", "<i>")
        txt = txt.replace("&lt;/i&gt;", "</i>")
        txt = txt.replace("&lt;h2&gt;", "<h2>")
        txt = txt.replace("&lt;/h2&gt;", "</h2>")
        txt = txt.replace("&lt;h3&gt;", "<h3>") 
        txt = txt.replace("&lt;/h3&gt;", "</h3>")
        txt = txt.replace("&lt;li&gt;", "<li>") 
        txt = txt.replace("&lt;/li&gt;", "</li>")
        #txt = txt.replace("&lt;", "<") 
        #txt = txt.replace("&gt;", ">")
        txt = strippedtxt(txt)
        return txt
