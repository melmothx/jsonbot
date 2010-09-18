# gozerlib/gae/web/bot.py
#
#

""" GAE web bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.outputcache import add
from gozerlib.utils.generic import toenc, fromenc

## basic imports

import logging

## classes

class WebBot(BotBase):

    """ webbot just inherits from botbase for now. """

    def __init__(self, cfg=None, users=None, plugs=None, botname="gae-web", *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, botname, *args, **kwargs)
        if self.cfg: self.cfg['type'] = u'web'
        self.isgae = True
        self.type = u"web"

    def _raw(self, txt, response=None, end=u""):
        """  put txt to the client. """
        if txt and response: 
            logging.warn(u'web - OUT - %s' % unicode(txt))
            response.out.write(toenc(txt + end))

    def outnocb(self, channel, txt, response=None, *args, **kwargs):
        if not response: return
        if "http://" in txt:
            for item in re_url_match.findall(txt):
                 logging.debug("web - raw - found url - %s" % item)
                 txt = re.sub(item, '<a href="%s" onclick="window.open(\'%s\'); return false;">%s</a>' % (item, item, item), txt)
        self._raw(txt, response)
     
