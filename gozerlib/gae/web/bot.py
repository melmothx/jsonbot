# gozerlib/web/bot.py
#
#

""" web bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.outputcache import add

class WebBot(BotBase):

    """ webbot just inherits from botbase for now. """

    def __init__(self, cfg=None, users=None, plugs=None, *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, *args, **kwargs)
        if self.cfg:
            self.cfg['type'] = 'web'
        self.type = "web"

    def say(self, channel, txt, *args, **kwargs):
        add(channel, [txt, ])

    def sayroot(self, channel, txt, *args, **kwargs):
        add(channel, [txt, ])
