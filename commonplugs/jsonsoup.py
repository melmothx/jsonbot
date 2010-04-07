# commonplugs/jsonsoup.py
#
#

## gozerlib imports

from gozerlib.callbacks import callbacks
from gozerlib.utils.url import posturl, getpostdata
from gozerlib.persiststate import PlugState
from gozerlib.commands import cmnds
from gozerlib.socket.irc.monitor import outmonitor
from gozerlib.socket.rest.server import RestServer, RestRequestHandler
from gozerlib.eventbase import EventBase
from gozerlib.utils.exception import handle_exception
from gozerlib.examples import examples

## simplejson imports

from simplejson import dumps

## basic imports

import socket
import re
import logging

## VARS

outurl = "http://jsonsoup.appspot.com/soup/"

state = PlugState()

if not state.data.relay:
    state.data.relay = []

if not state.data.outs:
    state.data.outs = [outurl, ]

## callbacks

def preremote(bot, event):

    if event.channel in state.data.relay:
        return True

def handle_doremote(bot, event):

    if event.isremote:
        return

    e = RemoteEvent(bot.server, event.tojson())
    e.makeid()

    for url in state.data.outs:
        posturl(url, {}, e.tojson())

callbacks.add('PRIVMSG', handle_doremote, preremote, threaded=True)
callbacks.add('OUTPUT', handle_doremote, preremote, threaded=True)
callbacks.add('MESSAGE', handle_doremote, preremote, threaded=True)
callbacks.add('BLIP_SUBMITTED', handle_doremote, preremote, threaded=True)
outmonitor.add('soup', handle_doremote, preremote, threaded=True)

def handle_soup_on(bot, event):

    if not event.rest:
        target = event.channel
    else:
        target = event.rest

    if not target in state.data['relay']:
        state.data['relay'].append(target)
        state.save()

    event.done()

cmnds.add('soup-on', handle_soup_on, 'OPER')
examples.add('soup-on', 'enable relaying of the channel to the JSONBOT event network (jsonsoup)', 'soup-on')

def handle_soup_off(bot, event):

    if not event.rest:
        target = event.channel
    else:
        target = event.rest

    if target in state.data['relay']:
        state.data['relay'].remove(target)
        state.save()
    event.done()

cmnds.add('soup-off', handle_soup_off, 'OPER')
examples.add('soup-off', 'disable relaying of channel to the JSONBOT event network (jsonsoup)', 'soup-off')
