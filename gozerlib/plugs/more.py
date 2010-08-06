# plugs/more.py
#
#

""" access the output cache. """

from gozerlib.commands import cmnds
from gozerlib.examples import examples

def handle_more(bot, ievent):
    """ pop message from the output cache. """
    what, size = bot.outcache.more(ievent.channel)

    if not what:
        ievent.reply('no more data available for %s' % ievent.channel)
        return

    if size:
        txt = "%s (+%s)" % (what.strip(), size)
    else:
        txt = what.strip()

    if bot.type == 'web':
        ievent.reply(txt)
    else:
        bot.say(ievent.printto, txt, extend=5)
        
cmnds.add('more', handle_more, ['USER', 'GUEST', 'CLOUD'], threaded=True)
examples.add('more', 'return txt from output cache', 'more')
