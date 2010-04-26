# plugs/more.py
#
#

""" access the output cache. """

from gozerlib.commands import cmnds
from gozerlib.examples import examples

def handle_less(bot, ievent):
    """ get entry from the output cache. """
    try:
        if len(ievent.args) == 3:
            (who, index1, index2) = ievent.args
        elif len(ievent.args) == 2:
            who = ievent.userhost
            (index1, index2) = ievent.args
        else:
            who = ievent.userhost
            index1 = 0
            index2 = ievent.args[0]
        index1 = int(index1)
        index2 = int(index2)
    except IndexError:
        ievent.missing('[<who>] [<index1>] <index2>')
        return
    except ValueError:
        ievent.reply('i need integers as arguments')
        return

    txt = bot.outcache.get(who, index1, index2)

    if not txt:
        ievent.reply('no data available for %s %s %s' % \
(who, index1, index2))
        return

    ievent.reply(txt, raw=True)

#cmnds.add('less', handle_less, ['USER', 'CLOUD'])
#examples.add('less', "less [<who>] [<index1>] <index2> .. get txt from bots output cache", '1) less 0 2) less 0 2 3) less bart 1 0')

def handle_lesssize(bot, ievent):

    """ show size of output cache. """

    try:
        who = ievent.args[0]
    except IndexError:
        who = ievent.nick

    ievent.reply("outputcache for %s: %s" % (who, str(bot.outcache.size(who))))

#cmnds.add('less-size', handle_lesssize, ['USER', ])
#examples.add('less-size', "show sizes of data in bot's ouput cache", 'less-size')

def handle_more(bot, ievent):
    """ pop message from the output cache. """
    try:
        who = ievent.args[0]
    except IndexError:
        who = ievent.auth

    what, size = bot.outcache.more(who, 0)

    if not what:
        ievent.reply('no more data available for %s' % who)
        return

    #ievent.reply(what)

    if size:
        ievent.reply("%s (+%s)" % (what.strip(), size), raw=True)
    else:
        ievent.reply(what.strip(), raw=True)
     
cmnds.add('more', handle_more, ['USER', 'GUEST', 'CLOUD'], threaded=True)
examples.add('more', 'return txt from output cache', '1) more 2) more test')
