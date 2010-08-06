# plugs/more.py
#
#

""" access the output cache. """

from gozerlib.utils.generic import getwho
from gozerlib.commands import cmnds
from gozerlib.examples import examples

def handle_more(bot, ievent):
    """ pop message from the output cache. """
    try:
        w = ievent.args[0]
        who = getwho(bot, w)
    except IndexError:
        who = ievent.userhost

    what, size = bot.outcache.more(who, 0)

    if not what:
        ievent.reply('no more data available for %s' % who)
        return

    if size:
        txt = "%s (+%s)" % (what.strip(), size)
    else:
        txt = what.strip()

    if bot.type == 'web':
        txt = "<code>" + txt + "</code>"
        ievent.reply(txt)
    else:
        bot.say(ievent.printto, txt, extend=5)
        
cmnds.add('more', handle_more, ['USER', 'GUEST', 'CLOUD'], threaded=True)
examples.add('more', 'return txt from output cache', '1) more 2) more test')
