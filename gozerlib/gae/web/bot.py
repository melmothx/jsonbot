# gozerlib/gae/web/bot.py
#
#

""" GAE web bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.outputcache import add
from gozerlib.utils.generic import toenc, fromenc, strippedtxt
from gozerlib.utils.url import re_url_match
from gozerlib.utils.timeutils import hourmin
from gozerlib.channelbase import ChannelBase

## basic imports

import logging
import re
import cgi
import urllib
import time

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
        if not txt: return 
        logging.debug("%s - web - out - %s" % (self.name, txt))
        if response: response.out.write(toenc(txt + end))
        elif chan:
            from google.appengine.api import channel
            logging.warn("%s - sending to channel %s" % (self.name, chan))
            channel.send_message(chan, txt)
                
    def outnocb(self, channel, txt, how="cache", event=None, origin=None, response=None, dotime=False, *args, **kwargs):
        txt = self.normalize(txt)
        if event and not event.how == "background": 
            logging.warn("%s - out - %s" % (self.name, txt))             
            if how == "cache": add(channel, [txt, ])
        if True:
            if "http://" in txt:
                 for item in re_url_match.findall(txt):
                     logging.debug("web - raw - found url - %s" % item)
                     url = u'<a href="%s" onclick="window.open(\'%s\'); return false;"><b>%s</b></a>' % (item, item, item)
                     try: txt = re.sub(item, url, txt)
                     except ValueError:  logging.error("web - invalid url - %s" % url)
            if dotime: txt = "[%s] %s" % (hourmin(time.time()), txt)
            if not response: self.update_web(channel, txt)
            else: self._raw(txt, response)

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

    def update_web(self, channel, txt):
        import google
        chan = ChannelBase(channel, botname="gae-web")
        logging.warn("%s - webchannels are %s" % (self.name, chan.data.webchannels))
        remove = []
        for c in chan.data.webchannels:
            try:
                self._raw(txt, chan=c)
            except google.appengine.api.channel.channel.InvalidChannelClientIdError:
                remove.append(c)
        if remove:
            for c in remove: chan.data.webchannels.remove(c)
            chan.save()
