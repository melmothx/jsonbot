# jsb.plugs.socket/kickban.py
#
#

""" kickban functionality for IRC. """

## jsb imports

from jsb.utils.generic import getwho
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.callbacks import callbacks

## basic imports

import Queue
import time
import logging

## defines

bans      = {}
cachetime = 300
timeout   = 10 

## callbacks

def handle_367(bot, ievent):
    logging.debug('kickban - 367 - %s' % str(ievent))
    channel = ievent.arguments[1].lower()
    if not bot.name in bans or not channel in bans[bot.name]:
        return # not requested by this plugin
    bans[bot.name][channel].append(ievent.txt.split()[0])

def handle_mode(bot, ievent):
    logging.debug('kick-ban - mode - %s' % str(ievent))
    # [18 Jan 2008 13:41:29] (mode) cmnd=MODE prefix=maze!wijnand@2833335b.cc9dd561.com.hmsk postfix=#eth0-test +b *!*@je.moeder.ook arguments=[u'#eth0-test', u'+b', u'*!*@je.moeder.ook'] nick=maze user=wijnand userhost=wijnand@2833335b.cc9dd561.com.hmsk channel=#eth0-test txt= command= args=[] rest= speed=5 options={}

## functions

def get_bans(bot, channel):
    # :ironforge.sorcery.net 367 basla #eth0 *!*@71174af5.e1d1a3cf.net.hmsk eth0!eth0@62.212.76.127 1200657224
    # :ironforge.sorcery.net 367 basla #eth0 *!*@6ca5f0a3.14055a38.89.123.imsk eth0!eth0@62.212.76.127 1200238584
    # :ironforge.sorcery.net 368 basla #eth0 :End of Channel Ban List
    channel = channel.lower()
    if not bot.name in bans:
        bans[bot.name] = {}
    bans[bot.name][channel] = []
    queue368 = Queue.Queue()
    if not bot.wait:
        return
    bot.wait.register('368', channel, queue368)
    bot.sendraw('MODE %s +b' % (channel, ))
    # wait for End of Channel Ban List
    try:
        res = queue368.get(1, timeout)
    except Queue.Empty:
        return None
    return bans[bot.name][channel]

def get_bothost(bot):
    return getwho(bot, bot.nick).split('@')[-1].lower()

## commands

def handle_ban_list(bot, ievent):
    banslist = get_bans(bot, ievent.channel)
    if not banslist:
        ievent.reply('the ban list for %s is empty' % ievent.channel)
    else:
        ievent.reply('bans on %s: ' % ievent.channel, banslist, nr=True)

def handle_ban_remove(bot, ievent):
    channel = ievent.channel.lower()
    if len(ievent.args) != 1 or not ievent.args[0].isdigit():
        ievent.missing('<banlist index>')
        return
    if not bot.name in bans or not channel in bans[bot.name]:
        banslist = get_bans(bot, ievent.channel)
    else:
        banslist = bans[bot.name][channel]
        index = int(ievent.args[0])-1
        if len(banslist) <= index:
            ievent.reply('ban index out of range')
        else:
            unban = banslist[index]
            banslist.remove(unban)
            bot.sendraw('MODE %s -b %s' % (channel, unban))
            ievent.reply('unbanned %s' % (unban, ))

def handle_ban_add(bot, ievent):
    if not ievent.args:
        ievent.missing('<nick>')
        return
    if ievent.args[0].lower() == bot.nick.lower():
        ievent.reply('not going to ban myself')
        return
    userhost = getwho(bot, ievent.args[0])
    if userhost:
        host = userhost.split('@')[-1].lower()
        if host == get_bothost(bot):
            ievent.reply('not going to ban myself')
            return
        bot.sendraw('MODE %s +b *!*@%s' % (ievent.channel, host))
        ievent.reply('banned %s' % (host, ))
    else:
        ievent.reply('can not get userhost of %s' % ievent.args[0])

def handle_kickban_add(bot, ievent):
    if not ievent.args:
        ievent.missing('<nick> [<reason>]')
        return
    if ievent.args[0].lower() == bot.nick.lower():
        ievent.reply('not going to kickban myself')
        return
    userhost = getwho(bot, ievent.args[0])
    reason = len(ievent.args) > 1 and ' '.join(ievent.args[1:]) or 'Permban requested, bye'
    if userhost:
        host = userhost.split('@')[-1].lower()
        if host == get_bothost(bot):
            ievent.reply('not going to kickban myself')
            return
        bot.sendraw('MODE %s +b *!*@%s' % (ievent.channel, host))
        bot.sendraw('KICK %s %s :%s' % (ievent.channel, ievent.args[0], reason))
    else:
        ievent.reply('can not get userhost of %s' % ievent.args[0])

callbacks.add('367', handle_367)
callbacks.add('MODE', handle_mode)

cmnds.add('ban-add', handle_ban_add, 'OPER')
examples.add('ban-add', 'adds a host to the ban list', 'ban-add *!*@lamers.are.us')
cmnds.add('ban-list', handle_ban_list, 'OPER', threaded=True)
cmnds.add('ban-remove', handle_ban_remove, 'OPER', threaded=True)
examples.add('ban-remove', 'removes a host from the ban list', 'ban-remove 1')
cmnds.add('ban-kickban', handle_kickban_add, 'OPER')
examples.add('ban-kickban', 'kickbans the given nick', 'kickban Lam0r Get out of here')
