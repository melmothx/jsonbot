# jsb/plugs/reverse.py
#
# 

__copyright__ = 'this file is in the public domain'
__author__ = 'Hans van Kranenburg <hans@knorrie.org>'

## jsb imports

from jsb.utils.generic import waitforqueue
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples

## basic imports

import types

## reverse command

def handle_reverse(bot, ievent):
    """ reverse string or pipelined list. """
    if not ievent.rest and ievent.inqueue: result = waitforqueue(ievent.inqueue, 5)
    elif not ievent.rest: ievent.missing('<text to reverse>') ; return
    else: result = ievent.rest
    if type(result) == types.ListType: ievent.reply("results: ", result[::-1])
    else: ievent.reply(result[::-1])

cmnds.add('reverse', handle_reverse, ['USER', 'GUEST'])
examples.add('reverse', 'reverse text or pipeline', '1) reverse gozerbot 2) list | reverse')
