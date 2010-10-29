# waveplugs/watcher.py
#
#

""" watch waves through xmpp. a wave is called a channel here. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.callbacks import callbacks, remote_callbacks, last_callbacks, first_callbacks
from gozerlib.persist import PlugPersist
from gozerlib.fleet import fleet
from gozerlib.utils.exception import handle_exception
from gozerlib.examples import examples
from gozerlib.gae.wave.waves import Wave
from gozerlib.utils.locking import locked

## plugin imports

from commonplugs.chatlog import formatevent

## basic imports

import copy
import logging

## defines

cpy = copy.deepcopy

## classes

class Watched(PlugPersist):

    """ Watched object contains channels and subscribers. """

    def __init__(self, filename):
        PlugPersist.__init__(self, filename)
        self.data.channels = self.data.channels or {}
        self.data.whitelist = self.data.whitelist or []
        self.data.descriptions = self.data.descriptions or {}

    def subscribe(self, botname, type, channel, jid):
        """ subscrive a jid to a channel. """ 
        channel = channel.lower()
        jid = unicode(jid)
        if not self.data.channels.has_key(channel):
            self.data.channels[channel] = []
        if not [botname, type, jid] in self.data.channels[channel]:
            self.data.channels[channel].append([botname, type, jid])
            self.save()

        return True

    def unsubscribe(self, botname, type, channel, jid):
        """ unsubscribe a jid from a channel. """ 
        channel = channel.lower()
        try:
            self.data.channels[channel].remove([botname, type, unicode(jid)])
        except (KeyError, TypeError, ValueError):
            return False

        self.save()
        return True

    def reset(self, channel):
        """ unsubscribe a jid from a channel. """ 
        channel = channel.lower()
        self.data.channels[channel] = []
        self.save()
        return True

    def subscribers(self, channel):
        """ get all subscribers of a channel. """
        channel = channel.lower()
        try:
            return self.data.channels[channel]
        except KeyError:
            return []

    def check(self, channel):
        """ check if channel has subscribers. """
        channel = channel.lower()
        return self.data.channels.has_key(channel)

    def enable(self, channel):
        """ add channel to whitelist. """
        channel = channel.lower()
        if not channel in self.data.whitelist:
            self.data.whitelist.append(channel)
            self.save()

    def disable(self, channel):
        """ remove channel from whitelist. """
        channel = channel.lower()
        try:
            self.data.whitelist.remove(channel)
        except ValueError:
            return False

        self.save()
        return True

    def available(self, channel):
        """ check if channel is on whitelist. """
        channel = channel.lower()
        return channel in self.data.whitelist

    def channels(self, channel):
        """ return channels on whitelist. """
        channel = channel.lower()
        res = []
        for chan, targets in self.data.channels.iteritems():
            if channel in str(targets):
                res.append(chan)

        return res

## defines

watched = Watched('channels')

## functions

def writeout(botname, type, channel, txt):
    watchbot = fleet.byname(botname)
    if not watchbot: watchbot = fleet.makebot(type, botname)
    if watchbot: watchbot.outnocb(channel, txt)

## callbacks

def prewatchcallback(bot, event):
    """ watch callback precondition. """
    if event.isdcc: return False
    logging.debug("watcher - checking %s - %s" % (event.channel, event.userhost))
    if not event.channel: return False
    if not event.txt: return
    return watched.check(unicode(event.channel)) and event.how != "background" and event.forwarded

@locked
def watchcallback(bot, event):
    """ the watcher callback, see if channels are followed and if so send data. """
    if not event.allowwatch: logging.warn("watch - allowwatch is not set - ignoring %s" % event.userhost) ; return
    subscribers = watched.subscribers(event.channel)
    watched.data.descriptions[event.channel.lower()] = event.title
    logging.info("watcher - %s - %s" % (event.channel, str(subscribers)))
    for item in subscribers:
        try:
            (botname, type, channel) = item
        except ValueError: continue
        if channel.lower() not in event.allowwatch: logging.warn("watcher - allowwatch denied %s - %s" % (channel, event.allowwatch)) ; continue
        m = formatevent(bot, event)
        if m.nick == bot.nick or event.cbtype not in ['PRIVMSG', 'DISPATCH', 'MESSAGE', 'BLIP_SUBMITTED']: txt = u"[!] %s" % m.txt
        else: txt = u"[%s] %s" % (m.nick or event.nick or event.auth, m.txt)
        if txt.count('] [') > 2: logging.debug("watcher - %s - skipping %s" % (type, txt)) ; continue
        if bot.isgae:
            from google.appengine.ext.deferred import defer
            defer(writeout, botname, type, channel, txt)
        else: writeout(botname, type, channel, txt)

first_callbacks.add('BLIP_SUBMITTED', watchcallback, prewatchcallback)
first_callbacks.add('PRIVMSG', watchcallback, prewatchcallback)
first_callbacks.add('JOIN', watchcallback, prewatchcallback)
first_callbacks.add('PART', watchcallback, prewatchcallback)
first_callbacks.add('QUIT', watchcallback, prewatchcallback)
first_callbacks.add('NICK', watchcallback, prewatchcallback)
first_callbacks.add('OUTPUT', watchcallback, prewatchcallback)
first_callbacks.add('MESSAGE', watchcallback, prewatchcallback)
first_callbacks.add('CONSOLE', watchcallback, prewatchcallback)
first_callbacks.add('WEB', watchcallback, prewatchcallback)
first_callbacks.add('DISPATCH', watchcallback, prewatchcallback)

## commands

def handle_watcherstart(bot, event):
    """ [<channel>] .. start watching a target (channel/wave). """
    target = event.rest or event.origin or event.channel

    watched.subscribe(bot.name, bot.type, target, event.channel)
    if not target in event.chan.data.watched:
        event.chan.data.watched.append(target)
        event.chan.save()

    event.done()

cmnds.add('watcher-start', handle_watcherstart, 'OPER')
cmnds.add('watch', handle_watcherstart, 'USER')
examples.add('watcher-start', 'start watching a channel. ', 'watcher-start <channel>')

def handle_watcherreset(bot, event):
    """ [<channel>] .. stop watching a channel/wave. """
    watched.reset(event.channel)
    event.done()

cmnds.add('watcher-reset', handle_watcherreset, 'OPER')
examples.add('watcher-reset', 'stop watching', 'watcher-reset')

def handle_watcherstop(bot, event):
    """ [<channel>] .. stop watching a channel/wave. """
    if not event.rest:
        target = event.origin
    else:
        target = event.rest

    watched.unsubscribe(bot.name, bot.type, target, event.channel)
    if target in event.chan.data.watched:
        event.chan.data.watched.remove(target)
        event.chan.save()
    event.done()

cmnds.add('watcher-stop', handle_watcherstop, 'OPER')
examples.add('watcher-stop', 'stop watching a channel', 'watcher-stop #dunkbots')

def handle_watcherlist(bot, event):
    """ see what channels we are watching. """
    chans = watched.channels(event.channel)

    if chans:
        res = []
        for chan in chans: 
            try:
                res.append(chan)
            except KeyError:
                res.append(chan)

        event.reply("channels watched on %s: " % event.channel, res)

cmnds.add('watcher-list', handle_watcherlist, ['USER', 'GUEST'])
examples.add('watcher-list', 'show what channels we are watching', 'watcher-channels')

def handle_watchersubscribers(bot, event):
    """" show channels that are watching us. """
    event.reply("watchers for %s: " % event.channel, watched.subscribers(event.channel))

cmnds.add('watcher-subscribers', handle_watchersubscribers, ['USER', 'GUEST'])
examples.add('watcher-subscribers', 'show channels that are watching us. ', 'watcher-list')
