# plugs/more.py
#
#

""" access the output cache. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.less import outcache

## basic imports

import logging

## more command

def handle_more(bot, ievent):
    """ pop message from the output cache. """
    if ievent.msg: target = ievent.nick
    else: target = ievent.channel
    try: txt, size = outcache.more(u"%s-%s" % (bot.name, target))
    except IndexError: txt = None 
    if not txt:
        ievent.reply('no more data available for %s' % target)
        return
    if size: txt += "<b> - %s more</b>" % str(size)
    bot.outnocb(target, txt, response=ievent.response)
    bot.outmonitor(ievent.origin or ievent.userhost, ievent.channel, txt)

cmnds.add('more', handle_more, ['USER', 'GUEST'])
examples.add('more', 'return txt from output cache', 'more')
