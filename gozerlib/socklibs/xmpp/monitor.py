# gozerlib/socket/xmpp/monitor.py
#
#

""" monitors .. call callback on bot output. """

## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.monitor import Monitor
from gozerlib.eventbase import EventBase

## xmpp imports

from message import Message

## classes

class XMPPMonitor(Monitor):

    """ monitor jabber output """

    def handle(self, bot, event):
        """ fire jabber monitor callbacks. """
        try:
            e = Message()
            e.copyin(event)
            e.isreply = True
            e.iscmnd = True
            e.remotecmnd = True
            e.remoteout = bot.jid
            e.channel = event.to
            e.fromm = e['from'] = bot.jid
            e.nick = bot.nick
            e.botoutput = True
            Monitor.handle(self, bot, e)
        except AttributeError:
            handle_exception()

## defines

xmppmonitor = XMPPMonitor('xmppmonitor')
