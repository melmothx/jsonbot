# gozerlib/plugs/botevent.py
#
#

""" provide handling of host/tasks/botevent tasks. """

## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.tasks import taskmanager
from gozerlib.botbase import BotBase
from gozerlib.eventbase import EventBase
from gozerlib.utils.lazydict import LazyDict
from gozerlib.factory import BotFactory

## simplejson imports

from simplejson import loads

## basic imports

import logging

## boteventcb callback

def boteventcb(inputdict, request, response):
    logging.warn(inputdict)
    logging.warn(dir(request))
    logging.warn(dir(response))
    body = request.body
    logging.warn(body)
    payload = loads(body)
    try:
        botjson = payload['bot']
        logging.warn(botjson)
        cfg = LazyDict(loads(botjson))
        logging.warn(str(cfg))
        bot = BotFactory().create(cfg.type, cfg)
        logging.warn("botevent - created bot: %s" % bot.dump())
        eventjson = payload['event']
        logging.warn(eventjson)
        event = EventBase()
        event.update(LazyDict(loads(eventjson)))
        logging.warn("botevent - created event: %s" % event.dump())
        event.isremote = True
        event.notask = True
        bot.doevent(event)
    except Exception, ex: handle_exception()

taskmanager.add('botevent', boteventcb)
