# gozerlib/plugs/data.py
#
#

""" data dumper commands. """

## gozerlib imports

from gozerlib.commands import cmnds


def handle_dataevent(bot, event):
    event.reply(event.dump())

cmnds.add("data-event", handle_dataevent, "OPER")

def handle_datachan(bot, event):
    event.reply(event.chan.data.dump())

cmnds.add("data-chan", handle_datachan, "OPER")


def handle_databot(bot, event):
    event.reply(bot.data.dump())

cmnds.add("data-bot", handle_databot, "OPER")
