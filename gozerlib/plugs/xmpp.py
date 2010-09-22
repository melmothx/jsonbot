# gozerlib/plugs/xmpp.py
#
#

""" xmpp related commands. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.fleet import fleet

## xmpp-invite command

def handle_xmppinvite(bot, event):
    """ invite (subscribe to) a different user. """
    if not event.rest:
        event.missing("<list of jids>")
        return
    bot = fleet.getfirstjabber()
    if bot:
        for jid in event.args: bot.invite(jid)
        event.done()
    else: event.reply("can't find jabber bot in fleet")

cmnds.add("xmpp-invite", handle_xmppinvite, 'OPER')
examples.add("xmpp-invite", "invite a user.", "xmpp-invite jsoncloud@appspot.com")
