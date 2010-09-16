# gozerlib/plugs/gatekeeper.py
#
#

""" gatekeeper commands. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples

## commands

def handle_gatekeeperallow(bot, event):
    """ allow user on bot. """
    if not event.rest:
        event.missing("<userhost>")
        return
    bot.gatekeeper.allow(event.rest)
    event.done()

cmnds.add('gatekeeper-allow', handle_remoteallow, 'OPER')
examples.add('gatekeeper-allow', 'add JID of remote bot that we allow to receice events from', 'gatekeeper-allow jsonbot@appspot.com')

def handle_gatekeeperdeny(bot, event):
    """ deny user on bot. """
    if not event.rest:
        event.missing("<userhost>")
        return
    bot.gatekeeper.deny(event.rest)
    event.done()

cmnds.add('gatekeeper-deny', handle_remotedeny, 'OPER')
examples.add('gatekeeper-deny', 'remove JID of remote bot', 'gatekeeper-deny evilfscker@pissof.com')
