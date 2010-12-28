# jsb.plugs.socket/restserver.py
#
#

## jsb imports

from jsb.lib.callbacks import callbacks
from jsb.utils.url import posturl, getpostdata
from jsb.lib.persistconfig import PersistConfig
from jsb.lib.commands import cmnds
from jsb.lib.socklib.rest.server import RestServer, RestRequestHandler
from jsb.lib.eventbase import EventBase
from jsb.utils.exception import handle_exception
from jsb.lib.examples import examples

## basic imports

import socket
import re
import logging

## defines

enable = False

try:
    cfg = PersistConfig()
    cfg.define('enable', 0)
    cfg.define('host' , socket.gethostbyname(socket.getfqdn()))
    cfg.define('name' , socket.getfqdn())
    cfg.define('port' , 11111)
    cfg.define('disable', [])
    hp = "%s:%s" % (cfg.get('host'), cfg.get('port'))
    url = "http://%s" % hp
    if cfg.enable:
         enable = True
except AttributeError:
    # we are on the GAE
    enable = False

## server part

server = None

## functions

def startserver(force=False):
    if not enable:
        logging.debug("rest server is disabled")
        return

    global server 
    if server and not force:
        logging.debug("REST server is already running. ")
        return server

    try:
        server = RestServer((cfg.get('host'), cfg.get('port')), RestRequestHandler)

        if server:
            server.start()
            logging.warn('restserver - running at %s:%s' % (cfg.get('host'), cfg.get('port')))

            for mount in cfg.get('disable'):
                server.disable(mount)
        else:
            logging.error('restserver - failed to start server at %s:%s' % (cfg.get('host'), cfg.get('port')))

    except socket.error, ex:
        logging.warn('restserver - start - socket error: %s' % str(ex))

    except Exception, ex:
        handle_exception()

    return server

def stopserver():

    try:
        if not server:
            logging.debug('restserver - server is already stopped')
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

def handle_rest_start(bot, event):
    cfg['enable'] = 1
    cfg.save()
    startserver()
    event.done()

cmnds.add('rest-start', handle_rest_start, 'OPER')
examples.add('rest-start', 'start the REST server', 'rest-start')

def handle_rest_stop(bot, event):
    cfg['enable'] = 0
    cfg.save()
    stopserver()
    event.done()

cmnds.add('rest-stop', handle_rest_stop, 'OPER')
examples.add('rest-stop', 'stop the REST server', 'rest-stop')
