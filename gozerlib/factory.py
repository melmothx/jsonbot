# gozerlib/factory.py
#
#

""" Factory to produce instances of classes. """

## gozerlib imports

from gozerlib.errors import NoSuchBotType

## Factory base class

class Factory(object):
     pass

## BotFactory class

class BotFactory(Factory):

    def create(self, type, cfg):
        if type == 'xmpp' or type == 'jabber':
            try:
                from gozerlib.gae.xmpp.bot import XMPPBot
                bot = XMPPBot(cfg)
            except ImportError:   
                from gozerlib.socklib.xmpp.bot import SXMPPBot
                bot = SXMPPBot(cfg)
        elif type == 'sxmpp':
            from gozerlib.socklib.xmpp.bot import SXMPPBot
            bot = SXMPPBot(cfg)
        elif type == 'web':
            from gozerlib.gae.web.bot import WebBot
            bot = WebBot(cfg)
        elif type == 'wave': 
            from gozerlib.gae.wave.bot import WaveBot
            bot = WaveBot(cfg, domain=cfg.domain)
        elif type == 'irc':
            from gozerlib.socklib.irc.bot import IRCBot
            bot = IRCBot(cfg)
        elif type == 'console':
            from gozerlib.console.bot import ConsoleBot
            bot = ConsoleBot(cfg)
        elif type == 'base':
            from gozerlib.botbase import BotBase
            bot = BotBase(cfg)
        else: raise NoSuchBotType('%s bot .. unproper type %s' % (type, cfg.dump()))
        return bot
