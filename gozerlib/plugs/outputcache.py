# gozerlib/plugs/outputcache.py
#
#

from gozerlib.commands import cmnds
from gozerlib.outputcache import get, set
from gozerlib.callbacks import callbacks

def handle_outputcachepollerwave(bot, event):
     res = get(event.channel)

     for result in res:
         event.reply(result)

callbacks.add('POLLER', handle_outputcachepollerwave)
#gn_callbacks.add('POLLER', handle_outputcachepollerwave)

def handle_outputcachepollerweb(bot, event):
     res = get(event.channel)

     for result in res:
         event.reply(result)

callbacks.add('WEB', handle_outputcachepollerweb)
#callbacks.add('EXEC', handle_outputcachepollerweb)

def handle_outputcache(bot, event):
    res = get(event.channel)

    if res:

        for result in res:
            event.reply(result)

    else:
        event.reply('no data in cache')

cmnds.add('outputcache', handle_outputcache, 'USER')

def handle_outputcacheflush(bot, event):
 
    if not event.rest:
        target = event.channel
    else:
        target = event.rest

    set(target, [])
    event.done()

cmnds.add('outputcache-flush', handle_outputcacheflush, 'OPER')
