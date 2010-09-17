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
        if self.cfg:
            self.cfg['type'] = u'web'
        self.isgae = True
        self.type = u"web"

    def _raw(self, response, txt, end=u""):
        """  put txt to the client. """
        logging.warn(u'web - OUT - %s - %s' % (self.userhost, str(txt)))
        response.out.write(txt + end)
        
    def outnocb(self, channel, txt, *args, **kwargs):
        logging.debug(u"web - OUT - %s - %s" % (channel, txt))
        add(channel, [txt, ])
