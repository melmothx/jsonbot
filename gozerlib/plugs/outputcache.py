# gozerlib/plugs/outputcache.py
#
#

""" outputcache used when reply cannot directly be delivered. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.outputcache import get, set
from gozerlib.callbacks import callbacks
from gozerlib.examples import examples

## basic imports

import logging

## commands

def handle_outputcache(bot, event):
    """ forward the output cache to the user. """
    res = get(event.channel)
    logging.warn("outputcache - %s - %s" % (bot.type, len(res)))
    if res:
        for result in res:
            if result:
                bot.outnocb(event.channel, result, event.response)

cmnds.add('outputcache', handle_outputcache, ['OPER', 'USER', 'GUEST'])
examples.add('outputcache', 'forward the outputcache to the user.', 'outputcache')

def handle_outputcacheclear(bot, event):
    """ <channel or JID> .. flush outputcache of a channel. """
    set(event.channel, [])
    event.done()

cmnds.add('outputcache-clear', handle_outputcacheclear, 'USER')
examples.add('outputcache-clear', 'flush output cache of a channel', 'outputcache-clear')

def handle_outputcacheflush(bot, event):
    """ <channel or JID> .. flush outputcache of a user. """
    if not event.rest:
        target = event.channel
    else:
        target = event.rest

    set(target, [])
    event.done()

cmnds.add('outputcache-flush', handle_outputcacheflush, 'OPER')
examples.add('outputcache-flush', 'flush output cache of a user', '1) outputcache-flush 2) outputcache-flush bthate@gmail.com')
