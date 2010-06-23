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

    def say(self, channel, txt, *args, **kwargs):
        """ saying on a webbot add it to the output cache. """
        self.saynocb(channel, txt, *args, **kwargs)        
        self.outmonitor(self.name, channel, txt)

    def saynocb(self, channel, txt, *args, **kwargs):
        logging.debug(u"web - out - %s - %s" % (channel, txt))
        add(channel, [txt, ])
