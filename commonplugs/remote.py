# gozerlib/plugs/gozernet.py
#
#

""" events passed as json over xmpp. """

## gozerbot imports

from gozerlib.callbacks import callbacks
from gozerlib.utils.url import posturl, getpostdata
from gozerlib.persist import PlugPersist
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.utils.exception import handle_exception
from gozerlib.gozernet.bot import GozerNetBot
from gozerlib.config import cfg, Config

## simplejson imports

from simplejson import dumps

## basic imports

import socket
import re

## defines

outurl = "http://jsonbot.appspot.com/remote"
state = PlugPersist('remote')

if not state.data:
    state.data = {}

if not state.data.has_key('out'):
    state.data['out'] = [outurl, ]

if not state.data.has_key('forward'):
    state.data['forward'] = []

## commands

def handle_remote_addout(bot, event):
    """ add a bot (JID) to receive out events. """
    global state

    if not event.rest:
        event.missing('<JID>')
        return

    if not event.rest in state.data['out']:
        state.data['out'].append(event.rest)
        state.save()

    event.done()

cmnds.add('remote-addout', handle_remote_addout, 'OPER')

def handle_remote_delout(bot, event):
    """ stop sending events to another bot. """
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

cmnds.add('remote-delout', handle_remote_delout, 'OPER')

def handle_remote_outs(bot, event):
    """ show to which other bots we are sending. """
    event.reply(state.data['out'])

cmnds.add('remote-outs', handle_remote_outs, 'OPER')

def handle_remoteforward(bot, event):
    """ forward all events occuring on channel (wave) to the remotenet. """
    if not event.args:
        event.missing('<channel>')
        return

    state.data['forward'].append(event.args[0])
    state.save()
    event.done()

cmnds.add('remote-forward', handle_gozernetforward, 'OPER')
examples.add('remote-forward', 'add a forward item so that channels matching this get send over the remotenet', 'remote-forward #dunkbots')

def handle_remotedelforward(bot, event):
    """ stop forwarding a channel (wave) to the remotenet. """ 
    if not event.args:
        event.missing('<channel>')
        return

    try:
        state.data['forward'].remove(event.args[0])
        state.save()  
        event.done()
    except ValueError:
        event.reply("we are not forwarding %s" % event.args[0])

cmnds.add('remote-delforward', handle_remotedelforward, 'OPER')
examples.add('remote-delforward', 'remove a forward item so that channels matching this no longer get send over the remotenet', 'remote-delforward #dunkbots')

def handle_remotelistforward(bot, event):
    """ list all forwarded channels (waves). """
    event.reply("forwards: ", state.data['forward'])  

cmnds.add('remote-listforward', handle_remotelistforward, 'OPER') 
examples.add('remote-listforward', 'show forwards', 'remote-listforward')

def handle_remotecmnd(bot, event):
    """ do a command on the remotenet. """
    cmndstring = event.rest

    if not cmndstring:
        event.missing("<cmnd>")
        return

    gnbot = RemoteBot(state.data['out'])
    gnbot.cmnd(event, "!%s" % cmndstring)
    event.reply("sent to: ", gnbot.outs)

cmnds.add('cmnd', handle_gozernetcmnd, 'OPER') 
examples.add('cmnd', 'execute a command on the remotenet', 'cmnd version')
