# gozerlib/gae/web/bot.py
#
#

""" GAE web bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.outputcache import add

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
            logging.warn(u'web - OUT - %s' % str(txt))
            response.out.write(txt + end)

    def send(self, printto, txt, response=None, end=u""):
        if response:
            self._raw(txt, response)
            self.outmonitor(self.me, printto, txt)

    def sendnocb(self, printto, txt, response=None, end=u""):
        if response:
            self._raw(txt, response)
     
    def outnocb(self, channel, txt, *args, **kwargs):
        add(channel, [txt, ])
