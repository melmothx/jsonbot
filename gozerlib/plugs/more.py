# plugs/more.py
#
#

""" access the output cache. """

from gozerlib.commands import cmnds
from gozerlib.examples import examples

def handle_morestatus(bot, ievent):
    ievent.reply("%s more entries available" % len(ievent.chan.data.outcache))

cmnds.add('more-status', handle_morestatus, ['USER', 'OPER', 'GUEST'])
examples.add('more-status', "show nr op more items available", 'more-status')

def handle_more(bot, ievent):
    """ pop message from the output cache. """
    try:
        txt = ievent.chan.data.outcache.pop(0)
    except IndexError:
        txt = None 
    if not txt:
        ievent.reply('no more data available for %s' % ievent.channel)
        return

    ievent.chan.save()
    nritems = len(ievent.chan.data.outcache)
    if nritems:
        txt += "<b> - %s more</b>" % str(nritems)

    ievent.write(txt)

cmnds.add('more', handle_more, ['USER', 'GUEST', 'CLOUD'], threaded=True)
examples.add('more', 'return txt from output cache', 'more')

def handle_clear(bot, ievent):
    """ clear messages from the output cache. """
    ievent.chan.data.outcache = []
    ievent.chan.save()
    ievent.done()
     
cmnds.add('clear', handle_clear, ['USER', 'GUEST'], threaded=True)
examples.add('clear', 'clear the outputcache', 'clear')
