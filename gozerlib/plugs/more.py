# plugs/more.py
#
#

""" access the output cache. """

from gozerlib.commands import cmnds
from gozerlib.examples import examples

def handle_more(bot, ievent):
    """ pop message from the output cache. """
    txt = ievent.chan.data.outcache.pop(0)
 
    if not txt:
        ievent.reply('no more data available for %s' % ievent.channel)
        return
    
    ievent.chan.save()
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
