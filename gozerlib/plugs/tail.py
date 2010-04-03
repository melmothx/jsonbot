# gozerlib/plugs/tail.py
#
#

""" tail bot results. """

## gozerlib imports

from gozerlib.utils.generic import waitforqueue
from gozerlib.commands import cmnds
from gozerlib.examples import examples

## commands

def handle_tail(bot, ievent):
    """ used in a pipeline .. show last <nr> elements. """
    if not ievent.inqueue:
        ievent.reply("use tail in a pipeline")
        return
    try:
        nr = int(ievent.args[0])
    except (ValueError, IndexError):
        ievent.reply('tail <nr>')
        return

    result = waitforqueue(ievent.inqueue, 5)
    if not result:
        ievent.reply('no data to tail')
        return

    ievent.reply('results: ', result[-nr:])
    
cmnds.add('tail', handle_tail, ['USER', 'GUEST', 'CLOUD'], threaded=True)
examples.add('tail', 'show last <nr> lines of pipeline output', 'list | tail 5')
