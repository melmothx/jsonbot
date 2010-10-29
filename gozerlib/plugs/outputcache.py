# gozerlib/plugs/outputcache.py
#
#

""" outputcache used when reply cannot directly be delivered. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.outputcache import get, set, clear
from gozerlib.callbacks import callbacks
from gozerlib.examples import examples

## basic imports

import logging

## outputcache command

def handle_outputcache(bot, event):
    """ forward the output cache to the user. """
    res = get(event.channel)
    logging.warn("outputcache - %s - %s" % (bot.type, len(res)))
    if res:
        for result in res:
            if result:
                try: bot.outnocb(event.channel, result, response=event.response)
                except Exception, ex: logging.error("outputcache - %s - %s" % (str(ex), result))

cmnds.add('outputcache', handle_outputcache, ['USER', 'GUEST'])
examples.add('outputcache', 'forward the outputcache to the user.', 'outputcache')

## outputcache-clear

def handle_outputcacheclear(bot, event):
    """ flush outputcache of a channel. """
    clear(event.channel)
    event.done()

cmnds.add('outputcache-clear', handle_outputcacheclear, ['USER', 'GUEST'])
examples.add('outputcache-clear', 'flush output cache of a channel', 'outputcache-clear')
