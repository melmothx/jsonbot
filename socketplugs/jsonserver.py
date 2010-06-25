# socketplugs/jsonserver.py
#
#

## gozerlib imports

from gozerlib.callbacks import callbacks
from gozerlib.utils.url import posturl, getpostdata
from gozerlib.persiststate import PlugState
from gozerlib.commands import cmnds
from gozerlib.socklib.rest.server import RestServer, RestRequestHandler
from gozerlib.remote.event import RemoteEvent
from gozerlib.remote.bot import RemoteBot
from gozerlib.utils.exception import handle_exception
from gozerlib.examples import examples
from gozerlib.persist import Persist
from gozerlib.config import Config

## socketplugs imports

from socketplugs.restserver import startserver, stopserver

## simplejson imports

import simplejson
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
        path = request.path.split("gozerdata")[1]
    except (ValueError, IndexError):
        return dumps("can't find datapointer in path %s" % request.path)

    logging.warn("json.server - got path %s" % path)
    if len(path) > 2:
        path = 'gozerdata' + os.sep + path[1:]
        if '..' in path:
            return request.send_error(404)
        if not os.path.exists(path):
            logging.error("json.server - non existing file - %s" % path)
            request.send_error(404)
            return
 
        try:
            logging.warn("json.server - attempting to construct %s" % path)
            try:
                try:
                    result = Persist(path)
                    if result.data and result.data.public:
                        return dumps(result.data)
                    else:
                        request.send_error(404)
                except (TypeError, simplejson.decoder.JSONDecodeError):
                    result = Config(path)
                    logging.warn("json.server - got config - %s" % str(result))
                    if result and result.public:
                        try:
                            return dumps(result)
                        except TypeError:
                            request.send_error(404)
            except (IOError, TypeError):
                handle_exception()
                request.send_error(404)
                return
            request.send_error(404)
        except Exception, ex:
            handle_exception()
            request.send_error(500)
            return
    else:
        request.send_error(404)
        return

def start():
    ## we skip this for now as the server could still expose data that we dont want
    if True:
        return

    global server
    try:
        server = startserver()
    except socket.gaierror:
        return
    if not server:
        return
    try:
        server.addhandler('/gozerdata/', 'GET', json_GET)
        server.addhandler('/favicon.ico', 'GET', json_GET)
        server.enable('/gozerdata/')
    except Exception, ex:
        handle_exception()
     
## plugin init

def init():
    start()

def shutdown():
    global server
    if server:
        server.disable('/gozerdata/')

def handle_jsonserver_start(bot, event):
    """ add the /gozerdata/ mountpoints to the REST server. """
    init()
    event.done()

cmnds.add('jsonserver-start', handle_jsonserver_start, 'OPER')
examples.add('jsonserver-start', 'initialize the JSONBOT remote json data network server', 'jsonserver-start')

def handle_jsonserver_stop(bot, event):
    """ remove the /gozerdata/ mountpoints from the REST server. """
    shutdown()
    event.done()

cmnds.add('jsonserver-stop', handle_jsonserver_stop, 'OPER')
examples.add('jsonserver-stop', 'stop the JSONBOT remote json data server', 'jsonserver-stop')
