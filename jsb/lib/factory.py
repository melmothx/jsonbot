# jsb/factory.py
#
#

""" Factory to produce instances of classes. """

## jsb imports

from jsb.lib.errors import NoSuchBotType

## Factory base class

class Factory(object):
     pass

## BotFactory class

class BotFactory(Factory):

    def create(self, type, cfg):
        if type == 'xmpp' or type == 'jabber':
            try:
                from jsb.lib.gae.xmpp.bot import XMPPBot
                bot = XMPPBot(cfg)
            except ImportError:   
                from jsb.lib.socklib.xmpp.bot import SXMPPBot
                bot = SXMPPBot(cfg)
        elif type == 'sxmpp':
            from jsb.lib.socklib.xmpp.bot import SXMPPBot
            bot = SXMPPBot(cfg)
        elif type == 'web':
            from jsb.lib.gae.web.bot import WebBot
            bot = WebBot(cfg)
        elif type == 'wave': 
            from jsb.lib.gae.wave.bot import WaveBot
            bot = WaveBot(cfg, domain=cfg.domain)
        elif type == 'irc':
            from jsb.lib.socklib.irc.bot import IRCBot
            bot = IRCBot(cfg)
        elif type == 'console':
            from jsb.lib.console.bot import ConsoleBot
            bot = ConsoleBot(cfg)
        elif type == 'base':
            from jsb.lib.botbase import BotBase
            bot = BotBase(cfg)
        else: raise NoSuchBotType('%s bot .. unproper type %s' % (type, cfg.dump()))
        return bot
