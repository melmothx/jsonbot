# gozerlib/plugs/gozernet.py
#
#

""" json over xmpp. """

## gozerbot imports

from gozerlib.callbacks import callbacks
from gozerlib.utils.url import posturl, getpostdata
from gozerlib.persist import PlugPersist
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.utils.exception import handle_exception
from gozerlib.gozernet.bot import GozerNetBot

## simplejson imports

from simplejson import dumps

## basic imports

import socket
import re

## VARS

outxmpp = "primalsoup@gozerbot.org"
state = PlugPersist('gozernet')
gnbot = GozerNetBot()

if not state.data:
    state.data = {}

if not state.data.has_key('out'):
    state.data['out'] = [outxmpp, ]

if not state.data.has_key('forward'):
    state.data['forward'] = []

def handle_gozernet_addout(bot, event):

    global state

    if not event.rest:
        event.missing('<JID>')
        return

    if not event.rest in state.data['out']:
        state.data['out'].append(event.rest)
        state.save()

    event.done()

cmnds.add('gozernet-addout', handle_gozernet_addout, 'OPER')

def handle_gozernet_delout(bot, event):

    global state

    if not event.rest:
        event.missing('<JID>')
        return

    try:
        state.data['out'].remove(event.rest)
        state.save()
    except ValueError:
        pass

    event.done()

cmnds.add('gozernet-delout', handle_gozernet_delout, 'OPER')

def handle_gozernet_outs(bot, event):
    event.reply(state.data['out'])

cmnds.add('gozernet-outs', handle_gozernet_outs, 'OPER')

def handle_gozernetforward(bot, event):

    if not event.args:
        event.missing('<channel>')
        return

    state.data['forward'].append(event.args[0])
    state.save()
    event.done()

cmnds.add('gozernet-forward', handle_gozernetforward, 'OPER')
examples.add('gozernet-forward', 'add a forward item so that channels matching this get send over the gozernet', 'gozernet-forward #dunkbots')

def handle_gozernetdelforward(bot, event):

    if not event.args:
        event.missing('<channel>')
        return

    try:
        state.data['forward'].remove(event.args[0])
        state.save()  
        event.done()
    except ValueError:
        event.reply("we are not forwarding %s" % event.args[0])

cmnds.add('gozernet-delforward', handle_gozernetdelforward, 'OPER')
examples.add('gozernet-delforward', 'remove a forward item so that channels matching this no longer get send over the gozernet', 'gozernet-delforward #dunkbots')

def handle_gozernetlistforward(bot, event):
    event.reply("gozernet forwards: ", state.data['forward'])  

cmnds.add('gozernet-listforward', handle_gozernetlistforward, 'OPER') 
examples.add('gozernet-listforward', 'show gozernet forwards', 'gozernet-listforward')

def handle_gozernetcmnd(bot, event):

    cmndstring = event.rest

    if not cmndstring:
        event.missing("<cmnd>")
        return

    gnbot = GozerNetBot(target=bot, type="gozernet", outs=state.data['out'])
    gnbot.cmnd(event, "!%s" % cmndstring)
    event.reply("sent to: ", gnbot.outs)

cmnds.add('cmnd', handle_gozernetcmnd, 'OPER') 
examples.add('cmnd', 'execute a command on the gozernet', 'cmnd version')
