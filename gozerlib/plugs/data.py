# gozerlib/plugs/data.py
#
#

""" data dumper commands. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples

## commands

def handle_dataevent(bot, event):
    event.reply(event.dump())

cmnds.add("data-event", handle_dataevent, "OPER")
examples.add('data-event', 'dump event data', 'data-event')

def handle_datachan(bot, event):
    event.reply(event.chan.data.dump())

cmnds.add("data-chan", handle_datachan, "OPER")
examples.add('data-chan', 'dump channel data', 'data-chan')

def handle_databot(bot, event):
    event.reply(bot.data.dump())

cmnds.add("data-bot", handle_databot, "OPER")
examples.add('data-bot', 'dump bot data', 'data-bot')
