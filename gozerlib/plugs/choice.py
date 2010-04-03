# plugs/choice.py
#
#

""" the choice command can be used with a string or in a pipeline. """

## gozerlib imports

from gozerlib.utils.generic import waitforqueue
from gozerlib.commands import cmnds
from gozerlib.examples import examples

## basic imports

import random

def handle_choice(bot, ievent):
    """ make a random choice out of different words or list elements. """ 
    result = []
    if ievent.inqueue:
        result = waitforqueue(ievent.inqueue, 5)
    elif not ievent.args:
        ievent.missing('<space seperated list>')
        return
    else:
        result = ievent.args 

    if result:
        ievent.reply(random.choice(result))
    else:
        ievent.reply('nothing to choose from')

cmnds.add('choice', handle_choice, ['USER', 'GUEST', 'CLOUD'], threaded=True)
examples.add('choice', 'make a random choice', '1) choice a b c 2) list | choice')
