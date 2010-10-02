# gozerlib/plugs/chan.py
#
#

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.callbacks import callbacks

## chan-join command

def handle_chanjoin(bot, ievent):
    """ join a channel/wave"""
    try: channel = ievent.args[0]
    except IndexError:
        ievent.missing("<channel> [password]")   
        return
    try: password = ievent.args[1] 
    except IndexError: password = None
    bot.join(channel, password=password)
    ievent.done()

cmnds.add('chan-join', handle_chanjoin, ['OPER', 'JOIN'])
cmnds.add('join', handle_chanjoin, ['OPER', 'JOIN'])
examples.add('chan-join', 'chan-join <channel> [password]', '1) chan-join #test 2) chan-join #test mekker')

## chan-del command

def handle_chandel(bot, ievent):
    """ remove channel from bot.state['joinedchannels']. """
    try: chan = ievent.args[0].lower()
    except IndexError:  
        ievent.missing("<channel>")
        return
    try:
        if bot.state:
            bot.state.data['joinedchannels'].remove(chan)
            bot.state.save()
    except ValueError: pass
    ievent.done()

cmnds.add('chan-del', handle_chandel, 'OPER')
examples.add('chan-del', 'remove channel from bot.channels', 'chan-del #mekker')

## chan-part command

def handle_chanpart(bot, ievent):
    """ leave a channel. """
    if not ievent.rest: chan = ievent.channel
    else: chan = ievent.rest
    ievent.reply('leaving %s chan' % chan)
    bot.part(chan)
    try:
        if bot.state:
            bot.state.data['joinedchannels'].remove(chan)
            bot.state.save()
    except ValueError: pass
    ievent.done()

cmnds.add('chan-part', handle_chanpart, 'OPER')
cmnds.add('part', handle_chanpart, 'OPER')
examples.add('chan-part', 'chan-part [<channel>]', '1) chan-part 2) chan-part #test')

## channels command

def handle_channels(bot, ievent):
    """ channels .. show joined channels. """
    if bot.state: chans = bot.state['joinedchannels']
    else: chans = []
    if chans: ievent.reply("joined channels: ", chans)
    else: ievent.reply('no channels joined')

cmnds.add('channels', handle_channels, ['USER', 'WEB'])
examples.add('channels', 'show what channels the bot is on', 'channels')

## cycle command

def handle_chancycle(bot, ievent):
    """ cycle .. recycle channel. """
    ievent.reply('cycling %s' % ievent.channel)
    bot.part(ievent.channel)
    try: key = ievent.chan.data.password
    except (KeyError, TypeError): key = None
    bot.join(ievent.channel, password=key)  
    ievent.done()

cmnds.add('chan-cycle', handle_chancycle, 'OPER')
examples.add('chan-cycle', 'part/join channel', 'chan-cycle')

## chan-silent command

def handle_chansilent(bot, ievent):
    """ set silent mode of channel. """
    if ievent.rest: channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC': return
        channel = ievent.channel
    ievent.reply('putting %s to silent mode' % channel)
    ievent.chan.data.silent = True
    ievent.chan.save()
    ievent.done()

cmnds.add('chan-silent', handle_chansilent, 'OPER')
examples.add('chan-silent', 'set silent mode on channel the command was given in', 'chan-silent')

## chan-loud command

def handle_chanloud(bot, ievent):
    """ loud .. enable output to the channel. """
    if ievent.rest: channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC': return
        channel = ievent.channel
    ievent.reply('putting %s into loud mode' % ievent.channel)
    ievent.chan.data.silent= False
    ievent.chan.save()
    ievent.done()

cmnds.add('chan-loud', handle_chanloud, 'OPER')
examples.add('chan-loud', 'disable silent mode of channel command was given in', 'chan-loud')

## chan-withnotice comamnd

def handle_chanwithnotice(bot, ievent):
    """ withnotice .. make bot use notice in channel. """
    if ievent.rest: channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC': return
        channel = ievent.channel
    ievent.reply('setting notice in %s' % channel)
    ievent.chan.data.how  = "notice"
    ievent.chan.save()
    ievent.done()
    
cmnds.add('chan-withnotice', handle_chanwithnotice, 'OPER')
examples.add('chan-withnotice', 'make bot use notice on channel the command was given in', 'chan-withnotice')

## chan-withprivmsg

def handle_chanwithprivmsg(bot, ievent):
    """ withprivmsg .. make bot use privmsg in channel. """
    if ievent.rest: channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC': return
        channel = ievent.channel
    ievent.reply('setting privmsg in %s' % ievent.channel)
    try: bot.channels[channel]['notice'] = 0
    except (KeyError, TypeError):
        ievent.reply("no %s channel in database" % channel)
        return 
    ievent.done()

cmnds.add('chan-withprivmsg', handle_chanwithprivmsg, 'OPER')
examples.add('chan-withprivmsg', 'make bot use privmsg on channel command was given in', 'chan-withprivmsg')

## chan-mode command

def handle_channelmode(bot, ievent):
    """ show channel mode. """
    if bot.type != 'irc':
        ievent.reply('channelmode only works on irc bots')
        return
    try: chan = ievent.args[0].lower()
    except IndexError: chan = ievent.channel.lower()
    if not chan in bot.state['joinedchannels']:
        ievent.reply("i'm not on channel %s" % chan)
        return
    ievent.reply('channel mode of %s is %s' % (chan, bot.channels.get(chan, 'mode')))

cmnds.add('chan-mode', handle_channelmode, 'OPER')
examples.add('chan-mode', 'show mode of channel', '1) chan-mode 2) chan-mode #test')

## mode callback

def modecb(bot, ievent):
    """ callback to detect change of channel key. """
    if ievent.postfix.find('+k') != -1:
        key = ievent.postfix.split('+k')[1]
        ievent.chan.data.password = key
        ievent.chan.save()

callbacks.add('MODE', modecb)

## chan-denyplug command

def handle_chandenyplug(bot, event):
    if not event.rest: event.missing("<module name>") ; return
    if not event.rest in event.chan.data.denyplug:
        event.chan.data.denyplug.append(event.rest)
        event.chan.save()
        event.done()
    else: event.reply("%s is already being denied in channel %s" % (event.rest, event.channel))

cmnds.add("chan-denyplug", handle_chandenyplug, 'OPER')
examples.add("chan-denyplug", "deny a plugin command or callbacks to be executed in a channel", "chan-denyplug idle")

## chan-allowplug command

def handle_chanallowplug(bot, event):
    if not event.rest: event.missing("<module name>") ; return
    if event.rest in event.chan.data.denyplug:
        event.chan.data.denyplug.remove(event.rest)
        event.chan.save()
        event.done()
    else: event.reply("%s is already being allowed in channel %s" % (event.rest, event.channel))

cmnds.add("chan-allowplug", handle_chanallowplug, 'OPER')
examples.add("chan-allowplug", "allow a plugin command or callbacks to be executed in a channel", "chan-denyplug idle")
