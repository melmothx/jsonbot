# plugs/more.py
#
#

""" access the output cache. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples

## basic imports

import logging

## more command

def handle_more(bot, ievent):
    """ pop message from the output cache. """
    logging.warn("more - outputcache: %s" % bot.outcache.size(ievent.channel))
    try: txt, size = bot.outcache.more(ievent.channel)
    except IndexError: txt = None 
    if not txt:
        ievent.reply('no more data available for %s' % ievent.channel)
        return
    if size: txt += "<b> - %s more</b>" % str(size)
    bot.outnocb(ievent.channel, txt, response=ievent.response)
    bot.outmonitor(ievent.origin or ievent.userhost, ievent.channel, txt)

cmnds.add('more', handle_more, ['USER', 'GUEST'])
examples.add('more', 'return txt from output cache', 'more')
