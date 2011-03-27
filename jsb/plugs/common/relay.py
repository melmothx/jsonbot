# jsb.plugs.common/relay.py
#
#

""" relay to other users/channels/waves. """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.callbacks import first_callbacks
from jsb.lib.persist import PlugPersist
from jsb.lib.examples import examples
from jsb.lib.fleet import getfleet
from jsb.lib.errors import NoSuchWave
from jsb.utils.exception import handle_exception
from jsb.utils.generic import stripcolor

## basic imports

import logging
from copy import deepcopy as cpy

# plugin state .. this is where the relay plugin data lives. It's JSON string
# put into the database with memcache in between. The data is accessible
# through object.data. When data changes call object.save()
# see jsb/persist/persist.py

block = PlugPersist('block')
relay = PlugPersist('relay')

## CALLBACKS

# these are the callbacks that do the hard work of the relay plugin takes 
# place. The precondition is called to see whether the callback should fire 
# or not. It should return True or False.
# see jsb/callbacks.py
  
def relayprecondition(bot, event):
    """ check to see whether the callback needs to be executed. """
    if event.forwarded: return
    splitted = event.txt.split("]")
    try: bn = splitted[0][1:]
    except: bn = None
    if event.nick == bot.nick and not event.iscommand: logging.warn("relay - %s already relayed" % bot.nick) ; return
    origin = event.printto or event.channel
    logging.debug("relay - precondition - origin is %s" % origin)
    if event.txt:
        if origin and origin in relay.data: return True
    return False

# CORE BUSINESS

# this callback does all the relaying. It receives the event that triggered
# the callback and checks whether there are relays for the channel the event
# took place (the bot uses the users JID in the jabber and web case (web users
# must be registered)

def relaycallback(bot, event):
    """ this is the callbacks that handles the responses to questions. """
    # determine where the event came from
    origin = event.printto or event.channel
    try:
        # loop over relays for origin
        for botname, type, target in relay.data[origin]:
            try:
                logging.debug('trying relay of %s to (%s,%s)' % (origin, type, target))
                # tests to prevent looping
                if botname == bot.botname and origin == target: continue
                if bot.name in event.relayed: continue
                # check whether relay is blocked
                if block.data.has_key(origin):
                    if [botname, type, target] in block.data[origin]: continue
                # retrieve the bot from fleet (based on type)
                fleet = getfleet()
                outbot = fleet.byname(botname)
                if not outbot: outbot = fleet.makebot(type, botname)
                if outbot:
                    logging.debug('relay - outbot found - %s - %s' % (outbot.name, outbot.type))
                    # we got bot .. use it to send the relayed message
                    if event.nick == "bot":
                        txt = event.txt
                    else:
                        txt = "[%s] %s" % (event.nick, event.txt)
                    txt = stripcolor(txt)
                    outbot.outnocb(target, txt, event=event)
                else: logging.error("can't find %s bot" % type)
            except Exception, ex: handle_exception()
    except KeyError: pass

# MORE CORE BUSINESS
# this is the place where the callbacks get registered. The first argument is
# the string representation of the event type, MESSAGE is for jabber message,
# EXEC is for the gadget handling, WEB for the website, BLIP_SUBMITTED for
# wave and OUTPUT for the outputcache (both used in wave and web).

first_callbacks.add('MESSAGE', relaycallback, relayprecondition)
first_callbacks.add('EXEC', relaycallback, relayprecondition)
first_callbacks.add('WEB', relaycallback, relayprecondition)
first_callbacks.add('BLIP_SUBMITTED', relaycallback, relayprecondition)
first_callbacks.add('OUTPUT', relaycallback, relayprecondition)
first_callbacks.add('PRIVMSG', relaycallback, relayprecondition)

# COMMANDS
# this is where the commands for the relay plugin are defined, Arguments to a
# command function are the bot that the event occured on and the event that
# triggered the command. Think the code speaks for itself here ;]

def handle_relayclone(bot, event):
    """ clone relays from one channel to the other. """
    new = event.origin or event.channel
    try: old = event.args[0]
    except IndexError, ex: event.missing('<old target>') ; return
    try:
        relay.data[new] = list(relay.data[old])
        del relay.data[old]
        relay.save()
    except KeyError: event.reply("i didn't join the %s wave" % old) ; return
    except Exception, ex: handle_exception()
    event.done()

cmnds.add('relay-clone', handle_relayclone, 'OPER')
examples.add('relay-clone', 'clone relay of old wave to the new', 'relay-clone googlewave.com!w+Pu4YwndxA')

def handle_relay(bot, event):
    """ [<botname>] <type> <target> .. open a relay to a user. all input from us will be relayed. """
    try: (botname, type, target) = event.args
    except ValueError:
        try:
             botname = bot.name
             (type, target) = event.args
        except ValueError: event.missing('[<botname>] <bottype> <target>') ; return 
    origin = event.channel
    if not relay.data.has_key(origin): relay.data[origin] = []
    try:
        if not [type, target] in relay.data[origin]:
            relay.data[origin].append([botname, type, target])
            relay.save()
    except KeyError: relay.data[origin] = [[botname, type, target], ] ; relay.save()
    event.done()

cmnds.add('relay', handle_relay, 'USER')
examples.add('relay', 'open a relay to another user', 'relay bthate@gmail.com')

def handle_relaystop(bot, event):
    """ stop a relay to a user. all relaying to target will be ignore. """
    try: (botname, type, target) = event.args
    except ValueError:
        try:
            botname = bot.name
            (type, target) = event.args
        except (IndexError, ValueError): botname = bot.name ; type = bot.type ; target = event.channel 
    origin = event.origin or event.channel
    try:
        logging.debug('trying to remove relay (%s,%s)' % (type, target))
        relay.data[origin].remove([botname, type, target])
        relay.save()
    except (KeyError, ValueError): pass
    event.done()

cmnds.add('relay-stop', handle_relaystop, 'USER')
examples.add('relay-stop', 'close a relay to another user', 'relay-stop bthate@gmail.com')

def handle_relayclear(bot, event):
    """ clear all relays from a channel. all relaying to target will be ignored. """
    origin = event.origin or event.channel
    try:
        logging.debug('clearing relay for %s' % origin)
        relay.data[origin] = []
        relay.save()
    except (KeyError, ValueError): pass
    event.done()

cmnds.add('relay-clear', handle_relayclear, 'OPER')
examples.add('relay-clear', 'clear all relays from a channel', 'relay-clear')

def handle_askrelaylist(bot, event):
    """ show all relay's of a user. """
    origin = event.origin or event.channel
    try: event.reply('relays for %s: ' % origin, relay.data[origin])
    except KeyError: event.reply('no relays for %s' % origin)

cmnds.add('relay-list', handle_askrelaylist, 'USER')
examples.add('relay-list', 'show all relays of user/channel/wave.', 'relay-list')

def handle_relayblock(bot, event):
    """ <type> <target> .. block a user/channel/wave from relaying to us. """
    try: (type, target) = event.args
    except ValueError: event.missing('<type> <target>') ; return 
    origin = event.origin or event.channel
    if not block.data.has_key(origin): block.data[origin] = []
    if not [type, origin] in block.data[target]: block.data[target].append([type, origin]) ; block.save()
    event.done()

cmnds.add('relay-block', handle_relayblock, 'USER')
examples.add('relay-block', 'block a relay from another user', 'relay-block bthate@gmail.com')

def handle_relayunblock(bot, event):
    """ <target> .. remove a relay block of an user. """
    try: target = event.args[0]
    except IndexError: event.missing('<target>') ; return 
    origin = event.origin or event.channel
    try: block.data[origin].remove([bot.name, target]) ; block.save()
    except (KeyError, ValueError): pass
    event.done()

cmnds.add('relay-unblock', handle_relaystop, 'USER')
examples.add('relay-unblock', 'remove a block of another user', 'relay-unblock bthate@gmail.com')

def handle_relayblocklist(bot, event):
    """ show all blocks of a user/channel.wave. """
    origin = event.origin or event.channel
    try: event.reply('blocks for %s: ' % origin, block.data[origin])
    except KeyError: event.reply('no blocks for %s' % origin)

cmnds.add('relay-blocklist', handle_relayblocklist, 'USER')
examples.add('relay-blocklist', 'show blocked relays to us', 'relay-blocklist')
