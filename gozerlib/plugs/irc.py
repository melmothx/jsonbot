# gozerlib/plugs/irc.py
#
#

""" irc related commands. """

## gozerbot imports

from gozerlib.callbacks import callbacks
from gozerlib.socklib.partyline import partyline
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.fleet import fleet
import gozerlib.threads as thr

## basic imports

import Queue

## define

ignorenicks = []

## broadcast command

def handle_broadcast(bot, ievent):
    """ broadcast txt to all joined channels. """
    if not ievent.rest:
         ievent.missing('<txt>')
         return
    ievent.reply('broadcasting')
    fleet.broadcast(ievent.rest)
    partyline.say_broadcast(ievent.rest)
    ievent.reply('done')

cmnds.add('broadcast', handle_broadcast, 'OPER')
examples.add('broadcast', 'send a message to all channels and dcc users', 'broadcast good morning')

## join command

def dojoin(bot, ievent):
    """ join a channel/wave"""
    try: channel = ievent.args[0]
    except IndexError:
        ievent.missing("<channel> [password]")
        return
    try: password = ievent.args[1]
    except IndexError: password = None
    bot.join(channel, password=password)

cmnds.add('join', dojoin, ['OPER', 'JOIN'])
examples.add('join', 'join <channel> [password]', '1) join #test 2) join #test mekker')

## delchan command

def delchan(bot, ievent):
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

cmnds.add('delchan', delchan, 'OPER')
examples.add('delchan', 'delchan <channel> .. remove channel from bot.channels', 'delchan #mekker')

## part command

def dopart(bot, ievent):
    """ leave a channel. """
    if not ievent.rest: chan = ievent.channel
    else: chan = ievent.rest
    ievent.reply('leaving %s chan' % chan)
    bot.part(chan)
    ievent.done()

cmnds.add('part', dopart, 'OPER')
examples.add('part', 'part [<channel>]', '1) part 2) part #test')

## channels command

def handle_channels(bot, ievent):
    """ channels .. show joined channels. """
    if bot.state: chans = bot.state['joinedchannels']
    else: chans = []
    if chans: ievent.reply("joined channels: ", chans)
    else: ievent.reply('no channels joined')

cmnds.add('channels', handle_channels, ['USER', 'WEB'])
examples.add('channels', 'show what channels the bot is on', 'channels')

## chat command

def handle_chat(bot, ievent):
    """ chat .. start a bot initiated dcc chat session. """
    if not bot.type == 'irc':
        ievent.reply("chat only works on irc bots")
        return
    i = ievent
    thr.start_new_thread(bot._dcclisten, (i.nick, i.userhost, i.channel))
    ievent.reply('dcc chat request sent')

cmnds.add('chat', handle_chat, 'USER')
examples.add('chat', 'start a dcc chat session', 'chat')

## cycle command

def handle_cycle(bot, ievent):
    """ cycle .. recycle channel. """
    ievent.reply('cycling %s' % ievent.channel)
    bot.part(ievent.channel)
    try: key = ievent.chan.data.password
    except (KeyError, TypeError): key = None
    bot.join(ievent.channel, password=key)
    ievent.done()

cmnds.add('cycle', handle_cycle, 'OPER')
examples.add('cycle', 'part/join channel', 'cycle')

## jump command

def handle_jump(bot, ievent):
    """ change server. """
    if bot.jabber:
        ievent.reply('jump only works on irc bots')
        return
    if len(ievent.args) != 2:
        ievent.missing('<server> <port>')
        return
    (server, port) = ievent.args
    ievent.reply('changing to server %s' % server)
    bot.shutdown()
    bot.server = server
    bot.port = port
    bot.connect()
    ievent.done()

cmnds.add('jump', handle_jump, 'OPER')
examples.add('jump', 'jump <server> <port> .. switch server', 'jump localhost 6667')

## mode callback

def modecb(bot, ievent):
    """ callback to detect change of channel key. """
    if ievent.postfix.find('+k') != -1:
        key = ievent.postfix.split('+k')[1]
        ievent.chan.data.password = key
        ievent.chan.save()

callbacks.add('MODE', modecb)

## nick command

def handle_nick(bot, ievent):
    """ change bot's nick. """
    if bot.jabber:
        ievent.reply('nick works only on irc bots')
        return
    try: nick = ievent.args[0]
    except IndexError:
        ievent.missing('<nickname>')
        return
    ievent.reply('changing nick to %s' % nick)
    bot.donick(nick, setorig=1, save=1)
    ievent.done()

cmnds.add('nick', handle_nick, 'OPER', threaded=True)
examples.add('nick', 'nick <nickname> .. set nick of the bot', 'nick mekker')

## sendraw command

def handle_sendraw(bot, ievent):
    """ send raw text to the server. """
    ievent.reply('sending raw txt')
    bot._raw(ievent.rest)
    ievent.done()

cmnds.add('sendraw', handle_sendraw, 'SENDRAW')
examples.add('sendraw', 'sendraw <txt> .. send raw string to the server', 'sendraw PRIVMSG #test :yo!')

## nicks command

def handle_nicks(bot, ievent):
    """ return nicks on channel. """
    if bot.jabber:
        ievent.reply('nicks only works on irc bots')
        return
    try: chan = ievent.args[0]
    except IndexError: chan = ievent.channel
    queue = Queue.Queue()
    if bot.wait:
        wait353 = bot.wait.register('353', chan, queue)
        wait366 = bot.wait.register('366', chan, queue)
    result = ""
    ievent.reply('searching for nicks')
    bot.names(chan)
    if bot.wait:
        while(1):
            qres = queue.get()
            if qres == None: break
            if qres.cmnd == '366': break
            else: result += "%s " % qres.txt
    if bot.wait:
        bot.wait.delete(wait353)
        bot.wait.delete(wait366)
    if result:
        res = result.split()
        for nick in res:
            for i in ignorenicks:
                if i in nick:
                    try: res.remove(nick)
                    except ValueError: pass
        res.sort()
        ievent.reply("nicks on %s (%s): " % (chan, bot.server), res)
    else: ievent.reply("can't get nicks of channel %s" % chan)

cmnds.add('nicks', handle_nicks, ['OPER', 'WEB'], threaded=True)
examples.add('nicks', 'show nicks on channel the command was given in', 'nicks')

## silent command

def handle_silent(bot, ievent):
    """ set silent mode of channel. """
    if ievent.rest: channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC': return
        channel = ievent.channel
    ievent.reply('putting %s to silent mode' % channel)
    ievent.chan.data.silent = True
    ievent.chan.data.save()
    ievent.done()

cmnds.add('silent', handle_silent, 'OPER')
examples.add('silent', 'set silent mode on channel the command was given in', 'silent')

## loud command

def handle_loud(bot, ievent):
    """ loud .. enable output to the channel. """
    if ievent.rest: channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC': return
        channel = ievent.channel
    ievent.reply('putting %s into loud mode' % ievent.channel)
    ievent.chan.data.silent= False
    ievent.chan.save()
    ievent.done()

cmnds.add('loud', handle_loud, 'OPER')
examples.add('loud', 'disable silent mode of channel command was given in', 'loud')

## withnotice comamnd

def handle_withnotice(bot, ievent):
    """ withnotice .. make bot use notice in channel. """
    if ievent.rest: channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC': return
        channel = ievent.channel
    ievent.reply('setting notice in %s' % channel)
    ievent.chan.data.how  = "notice"
    ievent.chan.save()
    ievent.done()
    
cmnds.add('withnotice', handle_withnotice, 'OPER')
examples.add('withnotice', 'make bot use notice on channel the command was given in', 'withnotice')

## withrpivmsg

def handle_withprivmsg(bot, ievent):
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

cmnds.add('withprivmsg', handle_withprivmsg, 'OPER')
examples.add('withprivmsg', 'make bot use privmsg on channel command was given in', 'withprivmsg')

## reconnect command

def handle_reconnect(bot, ievent):
    """ reconnect .. reconnect to server. """
    ievent.reply('reconnecting')
    bot.reconnect()
    ievent.done()

cmnds.add('reconnect', handle_reconnect, 'OPER', threaded=True)
examples.add('reconnect', 'reconnect to server', 'reconnect')

## channelmode command

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

cmnds.add('channelmode', handle_channelmode, 'OPER')
examples.add('channelmode', 'show mode of channel', '1) channelmode 2) channelmode #test')

## action command

def handle_action(bot, ievent):
    """ make the bot send an action string. """
    try: channel, txt = ievent.rest.split(' ', 1)
    except ValueError:
        ievent.missing('<channel> <txt>')
        return
    bot.action(channel, txt)

cmnds.add('action', handle_action, ['ACTION', 'OPER'])
examples.add('action', 'send an action message', 'action #test yoo dudes')

## say command

def handle_say(bot, ievent):
    """ <channel> <txt> .. make the bot say something. """
    try: channel, txt = ievent.rest.split(' ', 1)
    except ValueError:
        ievent.missing('<channel> <txt>')
        return
    bot.say(channel, txt)

cmnds.add('say', handle_say, ['SAY', 'OPER'], speed=1)
examples.add('say', 'send txt to channel/user', 'say #test good morning')

## server command

def handle_server(bot, ievent):
    """ show the server to which the bot is connected. """
    ievent.reply(bot.server)

cmnds.add('server', handle_server, 'OPER')
examples.add('server', 'show server hostname of bot', 'server')

## voice command

def handle_voice(bot, ievent):
    """ <nick> .. give voice. """
    if bot.type != 'irc':
        ievent.reply('voice only works on irc bots')
        return
    if len(ievent.args)==0:
        ievent.missing('<nickname>')
        return
    ievent.reply('setting voide on %s' % str(ievent.args))
    for nick in sets.Set(ievent.args): bot.voice(ievent.channel, nick)
    ievent.done()

cmnds.add('voice', handle_voice, 'OPER')
examples.add('voice', 'give voice to user', 'voice test')
