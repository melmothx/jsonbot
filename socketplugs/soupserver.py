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

## socketplugs imports

from socketplugs.restserver import startserver, stopserver

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

## server part

server = None

def soup_POST(server, request):

    try:
        input = getpostdata(request)
        container = input['container']
    except KeyError, AttributeError:
        logging.warn("soup - %s - can't determine eventin" % request.ip)
        return dumps(["can't determine eventin"])

    event = EventBase()
    event.load(container)
    callbacks.check(event)
    return dumps(['ok',])

def soup_GET(server, request):
    try:
        path, container = request.path.split('#', 1)
    except ValueError:
        logging.warn("soup - %s - can't determine eventin" % request.ip)
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
        server.addhandler('/soup/', 'POST', soup_POST)
        server.addhandler('/soup/', 'GET', soup_GET)
    except Exception, ex:
        handle_exception()

## plugin init

def init():
    start()

def shutdown():
    global server
    if server:
        server.delhandler('/soup/', 'POST', soup_POST)
        server.delhandler('/soup/', 'GET', soup_GET)

def handle_soup_init(bot, event):
    """ add the /soup/ mountpoints to the REST server. """
    init()
    event.done()

cmnds.add('soup-init', handle_soup_init, 'OPER')
examples.add('soup-init', 'initialize the JSONBOT event network server', 'soup-init')

def handle_soup_disable(bot, event):
    """ remove the /soup/ mountpoints from the REST server. """
    shutdown()
    event.done()

cmnds.add('soup-disable', handle_soup_disable, 'OPER')
examples.add('soup-disable', 'stop the JSONBOT event network server', 'soup-disable')
