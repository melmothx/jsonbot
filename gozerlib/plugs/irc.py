# plugs/irc.py
#
#

""" irc related commands. """

__copyright__ = 'this file is in the public domain'
__gendocfirst__ = ['reconnect', 'join']
__gendoclast__ = ['part', ]

## gozerbot imports
from gozerlib.callbacks import callbacks
from gozerlib.socket.partyline import partyline
from gozerlib.commands import cmnds
from gozerlib.examples import examples
import gozerlib.threads as thr

## basic imports

import Queue

## define

ignorenicks = []

## commands

def handle_broadcast(bot, ievent):

    """ broadcast txt to all joined channels. """

    if not ievent.rest:
         ievent.missing('<txt>')
         return

    ievent.reply('broadcasting')
    partyline.say_broadcast(ievent.rest)
    ievent.reply('done')

cmnds.add('broadcast', handle_broadcast, 'OPER')
examples.add('broadcast', 'send a message to all channels and dcc users', 'broadcast good morning')

def handle_alternick(bot, ievent):

    """ set alternative nick used if nick is already taken. """

    try:
        nick = ievent.args[0]
    except IndexError:
        ievent.reply('alternick is %s' % bot.state['alternick'])
        return

    ievent.reply('changing alternick to %s' % nick)
    bot.state['alternick'] = nick
    bot.state.save()
    ievent.reply('done')

cmnds.add('alternick', handle_alternick, 'OPER')
examples.add('alternick', 'get/set alertnick' , '1) alternick 2) alternick jsonbot')

def dojoin(bot, ievent):

    """ join <channel> [password]. """

    try:
        channel = ievent.args[0]
    except IndexError:
        ievent.missing("<channel> [password]")
        return

    try:
        password = ievent.args[1]
    except IndexError:
        password = None

    bot.join(channel, password=password)

cmnds.add('join', dojoin, ['OPER', 'JOIN'])
examples.add('join', 'join <channel> [password]', '1) join #test 2) join #test mekker')

def delchan(bot, ievent):

    """ delchan <channel>  .. remove channel from bot.channels. """

    try:
        chan = ievent.args[0].lower()
    except IndexError:
        ievent.missing("<channel>")
        return

    try:
        if bot.state:
            bot.state.data['joinedchannels'].remove(chan)
            bot.state.save()
    except ValueError:
        pass

    try:
        if bot.channels:
            del bot.channels.data[chan]
            bot.channels.save()
    except KeyError:
        ievent.reply("no channel %s in database" % chan)

    ievent.done()

cmnds.add('delchan', delchan, 'OPER')
examples.add('delchan', 'delchan <channel> .. remove channel from bot.channels', 'delchan #mekker')

def dopart(bot, ievent):

    """ part [<channel>]. """

    if not ievent.rest:
        chan = ievent.channel
    else:
        chan = ievent.rest

    ievent.reply('leaving %s chan' % chan)
    bot.part(chan)
    ievent.done()

cmnds.add('part', dopart, 'OPER')
examples.add('part', 'part [<channel>]', '1) part 2) part #test')

def handle_channels(bot, ievent):

    """ channels .. show joined channels. """

    chans = bot.state['joinedchannels']

    if chans:
        ievent.reply("joined channels: ", chans, dot=True)
    else:
        ievent.reply('no channels joined')

cmnds.add('channels', handle_channels, ['USER', 'WEB'])
examples.add('channels', 'show what channels the bot is on', 'channels')

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

def handle_cycle(bot, ievent):

    """ cycle .. recycle channel. """

    ievent.reply('cycling %s' % ievent.channel)
    bot.part(ievent.channel)
    try:
        key = bot.channels[ievent.channel.lower()]['key']
    except (KeyError, TypeError):
        key = None

    bot.join(ievent.channel, password=key)
    ievent.done()

cmnds.add('cycle', handle_cycle, 'OPER')
examples.add('cycle', 'part/join channel', 'cycle')

def handle_jump(bot, ievent):

    """ jump <server> <port> .. change server. """

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

def modecb(bot, ievent):

    """ callback to detect change of channel key. """

    if ievent.postfix.find('+k') != -1:
        key = ievent.postfix.split('+k')[1]
        bot.channels[ievent.channel.lower()]['key'] = key

callbacks.add('MODE', modecb)

def handle_nick(bot, ievent):

    """ nick <nickname> .. change bot's nick. """

    if bot.jabber:
        ievent.reply('nick works only on irc bots')
        return

    try:
        nick = ievent.args[0]
    except IndexError:
        ievent.missing('<nickname>')
        return

    ievent.reply('changing nick to %s' % nick)
    bot.donick(nick, setorig=1, save=1)
    ievent.done()

cmnds.add('nick', handle_nick, 'OPER', threaded=True)
examples.add('nick', 'nick <nickname> .. set nick of the bot', 'nick mekker')

def handle_sendraw(bot, ievent):

    """ sendraw <txt> .. send raw text to the server. """

    ievent.reply('sending raw txt')
    bot._raw(ievent.rest)
    ievent.done()

cmnds.add('sendraw', handle_sendraw, 'SENDRAW')
examples.add('sendraw', 'sendraw <txt> .. send raw string to the server', \
'sendraw PRIVMSG #test :yo!')

def handle_nicks(bot, ievent):

    """ return nicks on channel. """

    if bot.jabber:
        ievent.reply('nicks only works on irc bots')
        return

    try:
        chan = ievent.args[0]
    except IndexError:
        chan = ievent.channel

    queue = Queue.Queue()
    # set callback for name info response
    if bot.wait:
        wait353 = bot.wait.register('353', chan, queue)
        # 366 is end of names response list
        wait366 = bot.wait.register('366', chan, queue)
    result = ""
    ievent.reply('searching for nicks')
    bot.names(chan)

    if bot.wait:
        while(1):
            qres = queue.get()
            if qres == None:
                break
            if qres.cmnd == '366':
                break
            else:
                result += "%s " % qres.txt

    if bot.wait:
        bot.wait.delete(wait353)
        bot.wait.delete(wait366)

    if result:
        res = result.split()

        for nick in res:
            for i in ignorenicks:
                if i in nick:
                    try:
                        res.remove(nick)
                    except ValueError:
                        pass

        res.sort()
        ievent.reply("nicks on %s (%s): " % (chan, bot.server), res)
    else:
        ievent.reply("can't get nicks of channel %s" % chan)

cmnds.add('nicks', handle_nicks, ['OPER', 'WEB'], threaded=True)
examples.add('nicks', 'show nicks on channel the command was given in', 'nicks')

def handle_silent(bot, ievent):

    """ set silent mode of channel. """

    if ievent.rest:
        channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC':
            return
        channel = ievent.channel

    ievent.reply('putting %s to silent mode' % channel)

    try:
        bot.channels[channel]['silent'] = 1
    except (KeyError, TypeError):
        ievent.reply("no %s channel in database" % channel)
        return 
    ievent.done()

cmnds.add('silent', handle_silent, 'OPER')
examples.add('silent', 'set silent mode on channel the command was given in', 'silent')

def handle_loud(bot, ievent):

    """ loud .. enable output to the channel. """

    if ievent.rest:
        channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC':
            return
        channel = ievent.channel

    ievent.reply('putting %s into loud mode' % ievent.channel)

    try:
        bot.channels[channel]['silent'] = 0
    except (KeyError, TypeError):
        ievent.reply("no %s channel in database" % channel)
        return 

    ievent.done()

cmnds.add('loud', handle_loud, 'OPER')
examples.add('loud', 'disable silent mode of channel command was given in', 'loud')

def handle_withnotice(bot, ievent):

    """ withnotice .. make bot use notice in channel. """

    if ievent.rest:
        channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC':
            return
        channel = ievent.channel

    ievent.reply('setting notice in %s' % channel)

    try:
        bot.channels[channel]['notice'] = 1
    except (KeyError, TypeError):
        ievent.reply("no %s channel in database" % channel)
        return 

    ievent.done()
    
cmnds.add('withnotice', handle_withnotice, 'OPER')
examples.add('withnotice', 'make bot use notice on channel the command was given in', 'withnotice')

def handle_withprivmsg(bot, ievent):

    """ withprivmsg .. make bot use privmsg in channel. """

    if ievent.rest:
        channel = ievent.rest.split()[0].lower()
    else:
        if ievent.cmnd == 'DCC':
            return
        channel = ievent.channel

    ievent.reply('setting privmsg in %s' % ievent.channel)

    try:
        bot.channels[channel]['notice'] = 0
    except (KeyError, TypeError):
        ievent.reply("no %s channel in database" % channel)
        return 

    ievent.done()

cmnds.add('withprivmsg', handle_withprivmsg, 'OPER')
examples.add('withprivmsg', 'make bot use privmsg on channel command was given in', 'withprivmsg')

def handle_reconnect(bot, ievent):

    """ reconnect .. reconnect to server. """

    ievent.reply('reconnecting')
    bot.reconnect()
    ievent.done()

cmnds.add('reconnect', handle_reconnect, 'OPER', threaded=True)
examples.add('reconnect', 'reconnect to server', 'reconnect')

def handle_channelmode(bot, ievent):

    """ show channel mode. """

    if bot.type != 'irc':
        ievent.reply('channelmode only works on irc bots')
        return

    try:
        chan = ievent.args[0].lower()
    except IndexError:
        chan = ievent.channel.lower()

    if not chan in bot.state['joinedchannels']:
        ievent.reply("i'm not on channel %s" % chan)
        return

    ievent.reply('channel mode of %s is %s' % (chan, bot.channels.get(chan, 'mode')))

cmnds.add('channelmode', handle_channelmode, 'OPER')
examples.add('channelmode', 'show mode of channel', '1) channelmode 2) channelmode #test')

def handle_action(bot, ievent):

    """ make the bot send an action string. """

    try:
        channel, txt = ievent.rest.split(' ', 1)
    except ValueError:
        ievent.missing('<channel> <txt>')
        return

    bot.action(channel, txt)

cmnds.add('action', handle_action, ['ACTION', 'OPER'])
examples.add('action', 'send an action message', 'action #test yoo dudes')

def handle_say(bot, ievent):

    """ make the bot say something. """

    try:
        channel, txt = ievent.rest.split(' ', 1)
    except ValueError:
        ievent.missing('<channel> <txt>')
        return

    bot.say(channel, txt)

cmnds.add('say', handle_say, ['SAY', 'OPER'], speed=1)
examples.add('say', 'send txt to channel/user', 'say #test good morning')

def handle_server(bot, ievent):

    """ show the server to which the bot is connected. """

    ievent.reply(bot.server)

cmnds.add('server', handle_server, 'OPER')
examples.add('server', 'show server hostname of bot', 'server')

def handle_voice(bot, ievent):

    """ give voice. """

    if bot.type != 'irc':
        ievent.reply('voice only works on irc bots')
        return

    if len(ievent.args)==0:
        ievent.missing('<nickname>')
        return

    ievent.reply('setting voide on %s' % str(ievent.args))

    for nick in sets.Set(ievent.args):
        bot.voice(ievent.channel, nick)

    ievent.done()

cmnds.add('voice', handle_voice, 'OPER')
examples.add('voice', 'give voice to user', 'voice test')
