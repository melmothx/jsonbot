# socketplugs/jsonserver.py
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
from gozerlib.persist import Persist

## socketplugs imports

from socketplugs.restserver import startserver, stopserver

## simplejson imports

from simplejson import dumps

## basic imports

import socket
import re
import logging
import os

## server part

server = None

def json_GET(server, request):
    try:
        path = request.path.split("jsondata")[1]
    except (ValueError, IndexError):
        return dumps("can't find datapointer in path %s" % request.path)
    logging.warn(path)    
    if len(path) > 2:
        try:
            logging.warn("attempting to construct %s" % path[1:])
            try:
                result = Persist('gozerdata' + os.sep + path[1:])
            except IOError:
                return dumps("can't find %s file" % path[1:])
            if result.data:
                return dumps(result.data)
            else:
                return dumps("can't find matching data for %s" % path[1:])
        except Exception, ex:
            handle_exception()
            request.send_error(500)
    else:
        request.send_error(404)

def start():
    global server
    server = startserver()
    if not server:
        return
    try:
        server.addhandler('/jsondata/', 'GET', json_GET)
        server.enable('/jsondata/')
    except Exception, ex:
        handle_exception()
     
## plugin init

def init():
    start()

def shutdown():
    global server
    if server:
        server.disable('/jsondata/')

def handle_jsonserver_start(bot, event):
    """ add the /jsondata/ mountpoints to the REST server. """
    init()
    event.done()

cmnds.add('jsonserver-start', handle_jsonserver_start, 'OPER')
examples.add('jsonserver-start', 'initialize the JSONBOT remote json data network server', 'jsonserver-start')

def handle_jsonserver_stop(bot, event):
    """ remove the /jsondata/ mountpoints from the REST server. """
    shutdown()
    event.done()

cmnds.add('jsonserver-stop', handle_jsonserver_stop, 'OPER')
examples.add('jsonserver-stop', 'stop the JSONBOT remote json data server', 'jsonserver-stop')
