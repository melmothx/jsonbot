# gozerlib/remote/bot.py
#
#

""" remote bot. handlers incoming nodes. """

## gozerlib imports

from gozerlib.utils.url import posturl, getpostdata
from gozerlib.botbase import BotBase
from event import RemoteEvent

import logging

class RemoteBot(BotBase):

    """ RemoteBot broadcasts events through HTTP POST calls. """

    def __init__(self, target=None, cfg=None, users=None, plugs=None, jid=None, outs=[], *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, jid, *args, **kwargs)
        if self.cfg:
            self.cfg['type'] = 'remote'
        self.type = "remote"
        self.outs = outs or []

    def addouts(self, outs):
        self.outs = self.outs.append(outs)
        return self

    def _raw(self, url, data, *args, **kwargs):
        posturl(url, {}, data)

    def broadcast(self, data, *args, **kwargs):
        for url in self.outs:
            self._raw(url, data, *args, **kwargs)

    def say(self, channel, txt, event={}, *args, **kwargs):
        logging.warn('remote - out - %s - %s' % (channel, txt))
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
        self.broadcast(re.dump(), *args, **kwargs)

    def cmnd(self, event, txt, *args, **kwargs):
        logging.warn('remote - cmnd - %s - %s - %s' % (str(self.target), self.outs, txt))
        re = RemoteEvent()
        re.copyin(event)
        re.isreply = True
        re.printto = event.userhost
        re.target = event.userhost
        re.txt = re.origtxt = txt
        re.iscmnd = True
        re.remotecmnd = True
        re.remoteout = self.jid
        re.bot = self.target
        self.broadcast(re.dump(), *args, **kwargs)
