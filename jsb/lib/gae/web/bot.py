# jsb/gae/web/bot.py
#
#

""" GAE web bot. """

## jsb imports

from jsb.lib.botbase import BotBase
from jsb.lib.outputcache import add
from jsb.utils.generic import toenc, fromenc, strippedtxt
from jsb.utils.url import re_url_match
from jsb.utils.timeutils import hourmin
from jsb.lib.channelbase import ChannelBase

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

    def _raw(self, txt, response, end=u"<br>"):
        """  put txt to the client. """
        if not txt: return 
        txt = txt + end
        logging.debug("%s - out - %s" % (self.name, txt))
        response.out.write(txt)

    def outnocb(self, channel, txt, how="cache", event=None, origin=None, response=None, dotime=False, *args, **kwargs):
        txt = self.normalize(txt)
        if event and event.how != "background":
            logging.warn("%s - out - %s" % (self.name, txt))
            #if how == "cache": add(channel, [txt, ])
        if "http://" in txt or "https://" in txt:
             for item in re_url_match.findall(txt):
                 logging.debug("web - raw - found url - %s" % item)
                 url = u'<a href="%s" onclick="window.open(\'%s\'); return false;">%s</a>' % (item, item, item)
                 try: txt = re.sub(item, url, txt)
                 except ValueError:  logging.error("web - invalid url - %s" % url)
        #if dotime: txt = "[%s] %s" % (hourmin(time.time()), txt)
        if response: self._raw(txt, response)
        else: self.update_web(channel, txt)

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

    def update_web(self, channel, txt, end="<br>"):
        from google.appengine.api.channel import channel as gchan
        chan = ChannelBase(channel, botname="gae-web")
        #logging.warn("%s - webchannels are %s" % (self.name, chan.data.webchannels))
        remove = []
        for c in chan.data.webchannels:
            try:
                if c:
                    logging.debug("%s - sending to channel %s" % (self.name, chan))
                    gchan.send_message(c, txt + end)
            except gchan.InvalidChannelClientIdError:
                remove.append(c)
        if remove:
            for c in remove: chan.data.webchannels.remove(c)
            chan.save()
