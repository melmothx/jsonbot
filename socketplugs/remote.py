# commonplugs/remote.py
#
#

## gozerlib imports

from gozerlib.callbacks import callbacks
from gozerlib.utils.url import posturl, getpostdata
from gozerlib.persiststate import PlugState
from gozerlib.commands import cmnds
from gozerlib.socket.irc.monitor import outmonitor
from gozerlib.socket.rest.server import RestServer, RestRequestHandler
from gozerlib.remote.event import RemoteEvent
from gozerlib.remote.bot import RemoteBot
from gozerlib.utils.exception import handle_exception
from gozerlib.examples import examples

## socketplugs imports

from socketplugs.restserver import startserver, stopserver

## simplejson imports

from simplejson import dumps

## basic imports

import socket
import re
import logging

## VARS

outurl = "http://jsonbot.appspot.com/remote/"

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
    bot = RemoteBot(state.data.outs)
    bot.broadcast(e)

callbacks.add('PRIVMSG', handle_doremote, preremote, threaded=True)
callbacks.add('OUTPUT', handle_doremote, preremote, threaded=True)
callbacks.add('MESSAGE', handle_doremote, preremote, threaded=True)
callbacks.add('BLIP_SUBMITTED', handle_doremote, preremote, threaded=True)
outmonitor.add('remote', handle_doremote, preremote, threaded=True)

## server part

server = None

def remote_POST(server, request):

    try:
        input = getpostdata(request)
        container = input['container']
    except KeyError, AttributeError:
        logging.warn("remote - %s - can't determine eventin" % request.ip)
        return dumps(["can't determine eventin"])

    event = EventBase()
    event.load(container)
    callbacks.check(event)
    return dumps(['ok',])

def remote_GET(server, request):
    try:
        path, container = request.path.split('#', 1)
    except ValueError:
        logging.warn("remote - %s - can't determine eventin" % request.ip)
        return dumps(["can't determine eventin", ])

    try:
        event = EventBase()
        event.load(container)
        callbacks.check(event)
    except Exception, ex:
        handle_exception()
    return dumps(['ok', ])

def start():
    global server 
    server = startserver()
    try:
        server.addhandler('/remote/', 'POST', remote_POST)
        server.addhandler('/remote/', 'GET', remote_GET)
    except Exception, ex:
        handle_exception()

## plugin init

def init():
    start()

def shutdown():
    global server
    if server:
        server.delhandler('/remote/', 'POST', soup_POST)
        server.delhandler('/remote/', 'GET', soup_GET)

def handle_remote_init(bot, event):
    """ add the /remote/ mountpoints to the REST server. """
    init()
    event.done()

cmnds.add('remote-init', handle_remote_init, 'OPER')
examples.add('remote-init', 'initialize the JSONBOT remote event network server', 'remote-init')

def handle_remote_disable(bot, event):
    """ remove the /remote/ mountpoints from the REST server. """
    shutdown()
    event.done()

cmnds.add('remote-disable', handle_remote_disable, 'OPER')
examples.add('remote-disable', 'stop the JSONBOT remote event network server', 'remote-disable')
