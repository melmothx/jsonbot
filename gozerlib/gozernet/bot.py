# gozerlib/gozernet/bot.py
#
#

""" gozernet bot. handlers incoming nodes. """

## gozerlib imports

from gozerlib.botbase import BotBase
from event import RemoteEvent

import logging

class GozerNetBot(BotBase):

    """ gozernet bot just inherits from xmpp bot for now. """

    def __init__(self, target=None, cfg=None, users=None, plugs=None, jid=None, outs=[], *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, jid, *args, **kwargs)
        if self.cfg:
            self.cfg['type'] = 'gozernet'
        self.type = "gozernet"
        self.outs = outs or []
        self.target = target or BotBase()

    def addouts(self, outs):
        self.outs = self.outs.append(outs)
        return self

    def say(self, channel, txt, event={}, *args, **kwargs):
        logging.warn('gozernet - out - %s - %s' % (channel, txt))
        re = RemoteEvent()

        if event:
            re.copyin(event)  
        else:
            re.userhost = "%s.%s" % (self.name, self.server or 'jsonbot.appspot.com')
            re.nick = self.name

        re.isreply = True
        re.iscallback = False
        re.fromm = self.jid  
        re.txt = re.origtxt = txt
        re.iscmnd = False
        re.botoutput = True
        re.isresponse = True
        re.remotecmnd = False
        re.bot = self.target
        self.target.say(channel, re.dump(), *args, **kwargs)

    def cmnd(self, event, txt, *args, **kwargs):
        logging.warn('gozernet - cmnd - %s - %s - %s' % (str(self.target), self.outs, txt))
        for jid in self.outs:
            re = RemoteEvent()
            re.copyin(event)
            re.isreply = True
            re.printto = jid
            re.target = jid
            re.txt = re.origtxt = txt
            re.iscmnd = True
            re.remotecmnd = True
            re.remoteout = self.jid
            re.bot = self.target
            self.target.say(jid, re.dump(), *args, **kwargs)
