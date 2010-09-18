# plugs/more.py
#
#

""" access the output cache. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples

## basic imports

import logging

def handle_morestatus(bot, ievent):
    ievent.reply("%s more entries available" % len(ievent.chan.data.outcache))

cmnds.add('more-status', handle_morestatus, ['USER', 'OPER', 'GUEST'])
examples.add('more-status', "show nr op more items available", 'more-status')

def handle_more(bot, ievent):
    """ pop message from the output cache. """
    logging.warn("more - outputcache: %s" % bot.outcache.size(ievent.channel))
    try:
        txt, size = bot.outcache.more(ievent.channel)
    except IndexError:
        txt = None 
    if not txt:
        ievent.reply('no more data available for %s' % ievent.channel)
        return
    if size: txt += "<b> - %s more</b>" % str(size)
    if bot.type == "web":
        bot.send(ievent.channel, txt, ievent.response)
    else:
        bot.outnocb(ievent.channel, txt)
    bot.outmonitor(ievent.origin or ievent.userhost, ievent.channel, txt)

cmnds.add('more', handle_more, ['USER', 'GUEST', 'CLOUD'])
examples.add('more', 'return txt from output cache', 'more')

def handle_clear(bot, ievent):
    """ clear messages from the output cache. """
    ievent.chan.data.outcache = []
    ievent.chan.save()
    ievent.done()
     
cmnds.add('clear', handle_clear, ['USER', 'GUEST'], threaded=True)
examples.add('clear', 'clear the outputcache', 'clear')
