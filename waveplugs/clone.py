# waveplugs/clone.py
#
#

""" clone the wave after x blips. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.callbacks import callbacks
from gozerlib.gae.wave.waves import Wave
from gozerlib.plugins import plugs

## basic imports

import logging

## callbacks

def clonepre(bot, event):
    if event.bottype == "wave":
        return True

def clonecallback(bot, event):
    wave = event.chan
    if wave.data.threshold != -1 and (wave.data.seenblips > wave.data.threshold):
        wave.data.threshold = -1
        newwave = wave.clone(bot, event, event.title)
        plugs.load('commonplugs.hubbub')
        feeds = plugs['commonplugs.hubbub'].watcher.clone(bot.name, bot.type, newwave.data.waveid, event.waveid)
        event.reply("this wave is continued to %s with the following feeds: %s" % (newwave.data.url, feeds))

callbacks.add("BLIP_SUBMITTED", clonecallback, clonepre)
callbacks.add('OUTPUT', clonecallback, clonepre)
