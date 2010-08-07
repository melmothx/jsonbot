# plugs/more.py
#
#

""" access the output cache. """

from gozerlib.commands import cmnds
from gozerlib.examples import examples

def handle_more(bot, ievent):
    """ pop message from the output cache. """
    what = ievent.chan.data.outcache
 
    if not what:
        ievent.reply('no more data available for %s' % ievent.channel)
        return
    
    txt = what.pop()

    if bot.type == 'web':
        ievent.reply(txt)
    else:
        bot.say(ievent.printto, txt, extend=5)

    ievent.chan.save()

cmnds.add('more', handle_more, ['USER', 'GUEST', 'CLOUD'], threaded=True)
examples.add('more', 'return txt from output cache', 'more')

def handle_clear(bot, ievent):
    """ clear messages from the output cache. """
    ievent.chan.data.outcache = []
    ievent.chan.save()
    ievent.done()
     
cmnds.add('clear', handle_clear, ['USER', 'GUEST'], threaded=True)
examples.add('clear', 'clear the outputcache', 'clear')
