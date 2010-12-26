# jsb/plugs/irc.py
#
#

""" irc related commands. """

## gozerbot imports

from jsb.lib.callbacks import callbacks
from jsb.lib.socklib.partyline import partyline
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.fleet import getfleet
import jsb.lib.threads as thr

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
    getfleet().broadcast(ievent.rest)
    partyline.say_broadcast(ievent.rest)
    ievent.reply('done')

cmnds.add('broadcast', handle_broadcast, 'OPER')
examples.add('broadcast', 'send a message to all channels and dcc users', 'broadcast good morning')

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
    bot.donick(nick, setorig=True, save=True)
    ievent.done()

cmnds.add('nick', handle_nick, 'OPER', threaded=True)
examples.add('nick', 'nick <nickname> .. set nick of the bot', 'nick mekker')

## sendraw command

def handle_sendraw(bot, ievent):
    """ send raw text to the server. """
    ievent.reply('sending raw txt')
    bot._raw(ievent.rest)
    ievent.done()

cmnds.add('sendraw', handle_sendraw, ['OPER', 'SENDRAW'])
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

cmnds.add('nicks', handle_nicks, ['USER'], threaded=True)
examples.add('nicks', 'show nicks on channel the command was given in', 'nicks')

## reconnect command

def handle_reconnect(bot, ievent):
    """ reconnect .. reconnect to server. """
    ievent.reply('reconnecting')
    bot.reconnect()
    ievent.done()

cmnds.add('reconnect', handle_reconnect, 'OPER', threaded=True)
examples.add('reconnect', 'reconnect to server', 'reconnect')

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
    ievent.reply(bot.server or "not connected.")

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
