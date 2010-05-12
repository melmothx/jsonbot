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
from gozerlib.gae.wave.waves import Wave

## basic imports

import logging

def handle_wavestart(bot, event):

    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return

    wave = event.chan
    event.reply("cloning ...")
    newwave = wave.clone(bot, event, participants=["jsonbot@appspot.com", event.userhost])

    if not newwave:
        event.reply("can't create new wave")
        return

    newwave.data.protected = True
    newwave.data.owner = event.userhost
    newwave.save()
    event.reply("done")

cmnds.add('wave-start', handle_wavestart, 'USER')
examples.add('wave-start', 'start a new wave', 'wave-start')

def handle_waveclone(bot, event):

    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return

    wave = event.chan
    event.reply("cloning ...")
    newwave = wave.clone(bot, event, event.root.title.strip(), True)
    if not newwave:
        event.reply("can't create new wave")
        return
    plugs.load('commonplugs.hubbub')
    feeds = plugs['commonplugs.hubbub'].watcher.clone(bot.name, bot.type, newwave.data.waveid, event.waveid)
    event.reply("this wave is continued to %s with the following feeds: %s" % (newwave.data.url, feeds))

cmnds.add('wave-clone', handle_waveclone, 'USER')
examples.add('wave-clone', 'clone the wave', 'wave-clone')

def handle_wavenew(bot, event):

    if event.bottype != "wave":
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

    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return

    event.root.participants.add('public@a.gwave.com')
    event.done()

cmnds.add('wave-public', handle_wavepublic, 'USER')
examples.add('wave-public', 'make the wave public', 'wave-public')

def handle_waveinvite(bot, event):
    if event.bottype != "wave":
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
    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return
    event.reply(event.waveid)

cmnds.add('wave-id', handle_waveid, 'USER')
examples.add('wave-id', 'show the id of the wave the command is given in.', 'wave-id')

def handle_waveurl(bot, event):
    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return
    event.reply(event.url)

cmnds.add('wave-url', handle_waveurl, 'USER')
examples.add('wave-url', 'show the url of the wave the command is given in.', 'wave-url')

def handle_waveparticipants(bot, event):
    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return
    event.reply("participants: ", list(event.root.participants))

cmnds.add('wave-participants', handle_waveparticipants, 'USER')
examples.add('wave-participants', 'show the participants of the wave the command is given in.', 'wave-participants')

def handle_wavepart(bot, event):
    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return

    event.reply('bye')

cmnds.add('wave-part', handle_wavepart, 'OPER')
examples.add('wave-part', 'leave the wave', 'wave-part')

def handle_wavetitle(bot, event):
    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return

    if not event.rest:
        event.missing("<title>")
        return

    event.set_title(event.rest)
    event.reply('done')

cmnds.add('wave-title', handle_wavetitle, 'OPER')
examples.add('wave-title', 'set title of the wave', 'wave-title')

def handle_wavedata(bot, event):
    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return

    wave = event.chan
    if wave:
        data = dict(wave.data)
        del data['passwords']
        del data['json_data']
        event.reply(str(data))
    else:
        event.reply("can't fetch wave data of wave %s" % wave.waveid)

cmnds.add('wave-data', handle_wavedata, 'OPER')
examples.add('wave-data', 'show the waves stored data', 'wave-data')

def handle_wavethreshold(bot, event):
    if event.bottype != "wave":
        event.reply("this command only works in google wave.");
        return

    try:
        nrblips = int(event.rest)
    except ValueError:
        nrblips = -1

    wave = event.chan
    if wave:
        if nrblips == -1:
            event.reply('threshold of "%s" is %s' % (wave.data.title, str(wave.data.threshold)))
            return
        wave.data.threshold = nrblips
        wave.save()
        event.reply('threshold of "%s" set to %s' % (wave.data.title, str(wave.data.threshold)))

cmnds.add('wave-threshold', handle_wavethreshold, 'OPER')
examples.add('wave-threshold', 'set nr of blips after which we clone the wave', 'wave-threshold')

def handle_wavewhitelistadd(bot, event):
    if not event.rest:
        event.missing("<id>")
        return

    target = event.rest
    if not event.chan.data.whitelist:
        event.chan.data.whitelist = []
    if target not in event.chan.data.whitelist:
        event.chan.data.whitelist.append(target)
        event.chan.save()
    event.reply("done")

cmnds.add("wave-whitelistadd", handle_wavewhitelistadd, "OPER")
examples.add("wave-whitelistadd", "add a user to the waves whitelist", "wave-whitelistadd bthate@googlewave.com")

def handle_wavewhitelistdel(bot, event):
    if not event.rest:
        event.missing("<id>")
        return

    target = event.rest
    if not event.chan.data.whitelist:
        event.chan.data.whitelist = []
    if target in event.chan.data.whitelist:
        event.chan.data.whitelist.remove(target)
        event.chan.save()
    event.reply("done")

cmnds.add("wave-whitelistdel", handle_wavewhitelistdel, "OPER")
examples.add("wave-whitelistdel", "delete a user from the waves whitelist", "wave-whitelistdel bthate@googlewave.com")
