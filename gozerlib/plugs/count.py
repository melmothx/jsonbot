# gozerlib/plugs/count.py
#
#

""" count number of items in result queue. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.utils.generic import waitforqueue
from gozerlib.examples import examples

## count command

def handle_count(bot, ievent):
    """ show nr of elements in result list. """
    if not ievent.inqueue:
        ievent.reply("use count in a pipeline")
        return
    result = waitforqueue(ievent.inqueue, 5)
    ievent.reply(str(len(result)))

cmnds.add('count', handle_count, ['USER', 'GUEST', 'CLOUD'])
examples.add('count', 'count nr of items', 'list | count')
