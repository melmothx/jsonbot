# waveplugs/watcher.py
#
#

""" watch waves through xmpp. a wave is called a channel here. """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.callbacks import callbacks, gn_callbacks
from gozerlib.persist import PlugPersist
from gozerlib.gozernet.bot import GozerNetBot
from gozerlib.fleet import fleet
from gozerlib.utils.exception import handle_exception
from gozerlib.examples import examples
from gozerlib.gae.wave.waves import Wave

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
        jid = unicode(jid)
        if not self.data.channels.has_key(channel):
            self.data.channels[channel] = []
        if not [type, jid] in self.data.channels[channel]:
            self.data.channels[channel].append([botname, type, jid])
            self.save()

        return True

    def unsubscribe(self, botname, type, channel, jid):
        """ unsubscribe a jid from a channel. """ 
        try:
            self.data.channels[channel].remove([botname, type, unicode(jid)])
        except (KeyError, TypeError):
            return False

        self.save()
        return True

    def subscribers(self, channel):
        """ get all subscribers of a channel. """
        try:
            return self.data.channels[channel]
        except KeyError:
            return []

    def check(self, channel):
        """ check if channel has subscribers. """
        return self.data.channels.has_key(channel)

    def channels(self, channel):
        """ return all subscribers of a channel. """
        try:
            return self.data.channels[channel]
        except KeyError:
            return None

    def enable(self, channel):
        """ add channel to whitelist. """
        if not channel in self.data.whitelist:
            self.data.whitelist.append(channel)
            self.save()

    def disable(self, channel):
        """ remove channel from whitelist. """
        try:
            self.data.whitelist.remove(channel)
        except ValueError:
            return False

        self.save()
        return True

    def available(self, channel):
        """ check if channel is on whitelist. """
        return channel in self.data.whitelist

    def channels(self, channel):
        """ return channels on whitelist. """
        res = []
        for chan, targets in self.data.channels.iteritems():
            if channel in str(targets):
                res.append(chan)

        return res

## defines

watched = Watched('channels')

## callbacks

def prewatchcallback(bot, event):
    """ watch callback precondition. """
    logging.debug("watcher - pre - %s - %s - %s" % (event.channel, event.userhost, event.txt))
    return watched.check(event.channel) and event.txt

def watchcallback(bot, event):
    """ the watcher callback, see if channels are followed and if so send data. """
    if not event.txt:
        return

    subscribers = watched.subscribers(event.channel)
    watched.data.descriptions[event.channel] = event.title
    logging.debug("watcher - out - %s - %s" % (str(subscribers), event.txt))
    for item in subscribers:
        try:
            (botname, type, channel) = item
        except ValueError:
            continue

        watchbot = fleet.makebot(botname, type)
        if watchbot:
            orig = event.nick or event.userhost

            if event.cbtype == "OUTPUT":
                try:
                    from gozerlib.gae.wave.waves import Wave
                    wave = Wave(event.channel)
                except ImportError:
                    wave = None
                if wave:
                    txt = u"[%s] %s: %s" % (wave.data.title, event.ruserhost, event.txt)
                else:
                    txt = u"[%s] %s: %s" % (type, event.ruserhost, event.txt)
            else:
                txt = u"[%s] %s" % (orig, event.txt)

            logging.debug("watcher - %s - %s" % (type, txt))
            if txt.find('] [') > 1:
                continue

            watchbot.say(channel, txt)

gn_callbacks.add('BLIP_SUBMITTED', watchcallback, prewatchcallback)
callbacks.add('BLIP_SUBMITTED', watchcallback, prewatchcallback)
gn_callbacks.add('PRIVMSG', watchcallback, prewatchcallback)
#callbacks.add('PRIVMSG', watchcallback, prewatchcallback)
gn_callbacks.add('OUTPUT', watchcallback, prewatchcallback)
callbacks.add('OUTPUT', watchcallback, prewatchcallback)
gn_callbacks.add('MESSAGE', watchcallback, prewatchcallback)

## commands

def handle_watcherstart(bot, event):
    """ [<channel>] .. start watching a target (channel/wave). """
    if not event.rest:
        target = event.origin
    else:
        target = event.rest

    # you can only watch yourself on xmpp/wave
    if '@' in target and not event.userhost == target:
        event.reply('you are not allowed to watch %s' % target)
        return

    watched.subscribe(bot.name, bot.type, event.rest, event.channel)
    event.done()

    try:
        wave = Wave(event.rest)
        if wave:
            wavebot = fleet.makebot(type='wave')
            if wavebot:
                wave.say(wavebot, "%s is now watching %s" % (event.channel, event.rest))

    except Exception, ex:
        handle_exception()

cmnds.add('watcher-start', handle_watcherstart, 'USER')
examples.add('watcher-start', 'start watching a channel/wave. ', 'watcher-start <channel>')

def handle_watcherstop(bot, event):
    """ [<channel>] .. stop watching a channel/wave. """
    if not event.rest:
        target = event.origin
    else:
        target = event.rest

    watched.unsubscribe(bot.name, bot.type, target, event.channel)
    event.done()

cmnds.add('watcher-stop', handle_watcherstop, 'USER')
examples.add('watcher-stop', 'stop watching a channel', 'watcher-stop #dunkbots')

def handle_watcherchannels(bot, event):
    """ see what channels we are watching. """
    chans = watched.channels(event.channel)

    if chans:
        res = []
        for chan in chans: 
            try:
                res.append("%s (%s)" % (chan, watched.data.descriptions[chan]))
            except KeyError:
                res.append(chan)

        event.reply("channels watched on %s: " % event.channel, res)

cmnds.add('watcher-channels', handle_watcherchannels, ['USER'])
examples.add('watcher-channels', 'show what channels we are watching', 'watcher-channels')

def handle_watcherlist(bot, event):
    """" show channels that are watching us. """
    event.reply("watchers for %s: " % event.channel, watched.subscribers(event.channel))

cmnds.add('watcher-list', handle_watcherlist, ['USER'])
examples.add('watcher-list', 'show channels that are watching us. ', 'watcher-list')
