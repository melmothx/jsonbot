# commonplugs/quote.py
#
#

""" manage quotes. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.persist import PlugPersist

## basic imports

import random

## defines

quotes = PlugPersist('quotes.data')

if not quotes.data.index:
    quotes.data.index = 0

def handle_quoteadd(bot, event):
    """ add a quote. """
    quotes.data.index += 1
    quotes.data[quotes.data.index] = event.rest
    quotes.save()
    event.reply("quote %s added" % quotes.data.index)

cmnds.add('quote-add', handle_quoteadd, ['USER', 'OPER'])
examples.add('quote-add' , 'add a quote to the bot', 'quote-add blablabla')

def handle_quote(bot, event):
    """ get a quote. """
    possible = quotes.data.keys()
    possible.remove('index')
    if possible:
        nr = random.choice(possible)
        event.reply("#%s %s" % (nr, quotes.data[nr]))
    else:
        event.reply("no quotes yet.")

cmnds.add('quote', handle_quote, ['USER', 'OPER'])
examples.add('quote' , 'get a quote from the bot', 'quote')
