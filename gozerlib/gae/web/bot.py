# gozerlib/web/bot.py
#
#

""" web bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.outputcache import add

## classes

class WebBot(BotBase):

    """ webbot just inherits from botbase for now. """

    def __init__(self, cfg=None, users=None, plugs=None, *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, *args, **kwargs)
        if self.cfg:
            self.cfg['type'] = 'web'
        self.isgae = True
        self.type = "web"

    def say(self, channel, txt, *args, **kwargs):
        """ saying on a webbot add it to the output cache. """
        
        add(channel, [txt, ])
        self.outmonitor(self.name, channel, txt)

    def saynocb(self, channel, txt, *args, **kwargs):
        add(channel, [txt, ])
