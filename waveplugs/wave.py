# waveplugs/wave.py
#
#

""" wave related commands. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.utils.exception import handle_exception
from gozerlib.persist import PlugPersist
from gozerlib.callbacks import callbacks
from gozerlib.plugins import plugs

## basic imports

import logging

def handle_waveclone(bot, event):

    if event.type != "wave":
        event.reply("this command only works in google wave.");
        return

    #event.reply("cloning ...")
    title = event.root.title.strip()
    parts = list(event.root.participants)
    logging.warn('wave - clone - %s' % parts)
    newwave = bot.newwave(bot.domain, parts)
    newwave._set_title(title)
    for id in parts:
        newwave.participants.add(id)
    txt = event.rootblip.text
    newwave._root_blip.append(u'\n\n%s\n\n' % txt)
    blip = newwave.reply()
    blip.append("\nthis wave is cloned from %s\n" % event.url)

    for element in event.rootblip.elements:

        if element.type == 'GADGET':
            newwave._root_blip.append(element)

    wavelist = bot.submit(newwave)
    logging.warn("wave - clone - %s - submit returned %s" % (list(newwave.participants), str(wavelist)))

    if not wavelist:
        logging.warn("submit of new wave failed")
        return

    try:
        waveid = None
        for item in wavelist:
            try:
                waveid = item['data']['waveId']
            except (KeyError, ValueError):
                continue
        
        logging.warn("wave - newwave id is %s" % waveid)
        if waveid and 'sandbox' in waveid:
            url = "https://wave.google.com/a/wavesandbox.com/#restored:wave:%s" % waveid.replace('w+','w%252B')
        else:
            url = "https://wave.google.com/wave/#restored:wave:%s" % waveid.replace('w+','w%252B')
    except AttributeError:
        event.reply("no waveid found")
        return
        
    plugs.load('commonplugs.hubbub')
    feeds = plugs['commonplugs.hubbub'].watcher.clone(bot.name, waveid, event.waveid)
    event.reply("this wave is continued to %s with the following feeds: %s" % (url, feeds))
    continue_clone(event.waveid, waveid)

cmnds.add('wave-clone', handle_waveclone, 'USER')
examples.add('wave-clone', 'clone the wave', 'wave-clone')

def handle_wavenew(bot, event):

    if event.type != "wave":
        event.reply("this command only works in google wave.");
        return

    parts = ['jsonbot@appspot.com', event.userhost]
    newwave = bot.newwave(event.domain, parts)

    if event.rest:
        newwave.SetTitle(event.rest)

    event.done()

cmnds.add('wave-new', handle_wavenew, 'USER')
examples.add('wave-new', 'make a new wave', 'wave-new')

def handle_wavepublic(bot, event):

    if event.type != "wave":
        event.reply("this command only works in google wave.");
        return

    event.root.participants.add('public@a.gwave.com')
    event.done()

cmnds.add('wave-public', handle_wavepublic, 'USER')
examples.add('wave-public', 'make the wave public', 'wave-public')

def handle_waveinvite(bot, event):
    if event.type != "wave":
        event.reply("this command only works in google wave.");
        return

    if not event.rest:
        event.missing('<who>')
        return

    event.root.participants.add(event.rest)
    event.done()

cmnds.add('wave-invite', handle_waveinvite, 'USER')
examples.add('wave-invite', 'invite a user/bot into the wave', 'wave-invite bthate@googlewave.com')

def handle_waveid(bot, event):
    if event.type != "wave":
        event.reply("this command only works in google wave.");
        return
    event.reply(event.waveid)

cmnds.add('wave-id', handle_waveid, 'USER')
examples.add('wave-id', 'show the id of the wave the command is given in.', 'wave-id')

def handle_waveurl(bot, event):
    if event.type != "wave":
        event.reply("this command only works in google wave.");
        return
    event.reply(event.url)

cmnds.add('wave-url', handle_waveurl, 'USER')
examples.add('wave-url', 'show the url of the wave the command is given in.', 'wave-url')

def handle_waveparticipants(bot, event):
    if event.type != "wave":
        event.reply("this command only works in google wave.");
        return
    event.reply("participants: ", list(event.root.participants))

cmnds.add('wave-participants', handle_waveparticipants, 'USER')
examples.add('wave-participants', 'show the participants of the wave the command is given in.', 'wave-participants')

def handle_wavepart(bot, event):
    if event.type != "wave":
        event.reply("this command only works in google wave.");
        return

    event.reply('bye')

cmnds.add('wave-part', handle_wavepart, 'OPER')
examples.add('wave-part', 'leave the wave', 'wave-part')

continue_count = PlugPersist('continue-count')
continue_threshold = PlugPersist('continue-threshold')

def continue_clone(oldwave, newwave):
    try:
        continue_threshold.data[newwave] = continue_threshold.data[oldwave]
        continue_count.data[newwave] = 0
        continue_threshold.save()
        continue_count.save()
    except:
        pass

def continue_callback(bot, event):
    global continue_count
    global continue_threshold

    try:
        continue_count.data[event.channel] += 1
    except KeyError:
        continue_count.data[event.channel] = 1

    continue_count.save()

    try:

        if continue_count.data[event.channel] >= continue_threshold.data[event.channel]:
            continue_count.data[event.channel] = 0
            continue_count.save()
            event.reply("this wave is being continued (threshold = %s)" % continue_threshold.data[event.channel])
            event.submit()
            handle_waveclone(bot, event)
    except KeyError:
        pass

callbacks.add('BLIP_SUBMITTED', continue_callback)

def handle_waveblipcount(bot, event):
    event.reply(continue_count.data[event.channel])

cmnds.add('wave-blipcount', handle_waveblipcount, 'USER')

def handle_wavethreshold(bot, event):

    if event.type != "wave":
        event.reply("this command only works in google wave.");
        return

    try:
        count = int(event.args[0])
    except (IndexError, ValueError):
        event.reply("threshold of %s is %s" % (event.channel, continue_threshold.data[event.channel]))
        return

    if not continue_threshold.data:
        continue_threshold.data = {}

    continue_threshold.data[event.channel] = count
    continue_threshold.save()
    event.reply("threshold of %s is now %s" % (event.channel, count))

cmnds.add("wave-threshold", handle_wavethreshold, "OPER")
examples.add("wave-threshold", "set continue threshold of the wave .. after this many blips a new wave will be cloned.", "wave-threshold 200")

