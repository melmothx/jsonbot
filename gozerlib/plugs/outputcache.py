# gozerlib/plugs/outputcache.py
#
#

""" outputcache used when reply cannot directly be delivered. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.outputcache import get, set
from gozerlib.callbacks import callbacks
from gozerlib.examples import examples

## callbacks

def handle_outputcachepollerwave(bot, event):
     """ callback used in gadget polling. """
     res = get(event.channel)
     for result in res:
         event.reply(result)

#callbacks.add('POLLER', handle_outputcachepollerwave)

def handle_outputcachepollerweb(bot, event):
     """ send outputcache when WEB event is triggered. """
     res = get(event.channel)

     for result in res:
         event.reply(result)

#callbacks.add('WEB', handle_outputcachepollerweb)
#callbacks.add('GADGET', handle_outputcachepollerweb)

## commands

def handle_outputcache(bot, event):
    """ forward the output cache to the user. """
    res = get(event.channel)
    if res:
        for result in res:
            event.reply(result)

cmnds.add('outputcache', handle_outputcache, 'USER')
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
