# gozerlib/gae/web/bot.py
#
#

""" GAE web bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.outputcache import add
from gozerlib.utils.generic import toenc, fromenc
from gozerlib.utils.url import re_url_match

## basic imports

import logging
import re

## classes

class WebBot(BotBase):

    """ webbot just inherits from botbase for now. """

    def __init__(self, cfg=None, users=None, plugs=None, botname="gae-web", *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, botname, *args, **kwargs)
        if self.cfg: self.cfg['type'] = u'web'
        self.isgae = True
        self.type = u"web"

    def _raw(self, txt, response=None, end=u"<br>"):
        """  put txt to the client. """
        if txt and response: 
            logging.warn(u'web - OUT - %s' % unicode(txt))
            response.out.write(toenc(txt + end))

    def outnocb(self, channel, txt, how="msg", event=None, origin=None, response=None, *args, **kwargs):
        if "http://" in txt:
            for item in re_url_match.findall(txt):
                 logging.debug("web - raw - found url - %s" % item)
                 txt = re.sub(item, '<a href="%s" onclick="window.open(\'%s\'); return false;">%s</a>' % (item, item, item), txt)
        if not response or how == 'cache':
            add(channel, [txt, ])
        else:
            self._raw(txt, response)
