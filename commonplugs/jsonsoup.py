# commonplugs/jsonsoup.py
#
#

## gozerlib imports

from gozerlib.callbacks import callbacks
from gozerlib.utils.url import posturl, getpostdata
from gozerlib.persistconfig import PersistConfig
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

state = PersistConfig()

if not state.data:
    state.data = {}
if not state.data.has_key('relay'):
    state.data['relay'] = []

cfg = PersistConfig()
cfg.define('enable', 0)
cfg.define('host' , socket.gethostbyname(socket.getfqdn()))
cfg.define('name' , socket.getfqdn())
cfg.define('port' , 10102)
cfg.define('disable', [])

waitre = re.compile(' wait (\d+)', re.I)
hp = "%s:%s" % (cfg.get('host'), cfg.get('port'))
url = "http://%s" % hp

## callbacks

def preremote(bot, event):

    if event.channel in state.data['relay']:
        return True

def handle_doremote(bot, event):

    if event.isremote:
        return

    posturl(outurl, {}, {'event': event.tojson() })

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

def startserver():
    global server 

    try:
        server = RestServer((cfg.get('host'), cfg.get('port')), RestRequestHandler)

        if server:
            server.start()
            logging.warn('soup - running at %s:%s' % (cfg.get('host'), cfg.get('port')))
            server.addhandler('/soup/', 'POST', soup_POST)
            server.addhandler('/soup/', 'GET', soup_GET)

            for mount in cfg.get('disable'):
                server.disable(mount)

        else:
            logging.error('soup - failed to start server at %s:%s' % (cfg.get('host'), cfg.get('port')))

    except socket.error, ex:
        logging.warn('soup - start - socket error: %s' % str(ex))

    except Exception, ex:
        handle_exception()

def stopserver():

    try:
        if not server:
            logging.warn('soup - server is already stopped')
            return

        server.shutdown()

    except Exception, ex:
        handle_exception()
        pass

## plugin init

def init():

    if cfg['enable']:
        startserver()

def shutdown():

    if cfg['enable']:
        stopserver()

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

def handle_soup_startserver(bot, event):
    cfg['enable'] = 1
    cfg.save()
    startserver()
    event.done()

cmnds.add('soup-startserver', handle_soup_startserver, 'OPER')
examples.add('soup-startserver', 'start the JSONBOT event network server', 'soup-startserver')

def handle_soup_stopserver(bot, event):
    cfg['enable'] = 0
    cfg.save()
    stopserver()
    event.done()

cmnds.add('soup-stopserver', handle_soup_stopserver, 'OPER')
examples.add('soup-stopserver', 'stop the JSONBOT event network server', 'soup-startserver')
