# gozerlib/plugs/misc.py
#
#

""" misc commands. """

## gozerbot imports

from gozerlib.utils.exception import handle_exception
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.persiststate import UserState

## basic imports

import time
import os
import threading
import thread
import copy

cpy = copy.deepcopy

def handle_test(bot, ievent):
    """ give test response. """
    ievent.reply("%s .. it works!" % ievent.userhost)
    
cmnds.add('test', handle_test, ['USER', 'GUEST', ])
examples.add('test', 'give test response',' test')

def handle_testevent(bot, ievent):
    """ give dump of event. """
    event = cpy(ievent)
    try:
        del event.cfg
        del event.plugs
        del event.bot
    except Exception, ex:
        handle_exception()
    ievent.reply(str(event))
    
cmnds.add('test-event', handle_testevent, ['USER', 'GUEST', ])
examples.add('test-event', 'dump the event',' test-event')

def handle_source(bot, ievent):
    """ show where to fetch the bot source. """ 
    ievent.reply('see http://jsonbot.googlecode.com')

cmnds.add('source', handle_source, ['USER', 'GUEST'])
examples.add('source', 'show source url', 'source')

def handle_time(bot, ievent):
    """ show current time """
    authuser = username = ievent.userhost
    if authuser:
        userstate = UserState(username)
        try:
            tz = userstate['TZ']
        except KeyError:
            ievent.reply("%s doesn't have a timezone set .. use !set TZ " % username)
            return

        ievent.reply(get_time(tz, username, authuser))
    else:
        ievent.reply(get_time('UTC', '', ''))

cmnds.add('time', handle_time, ['USER', 'CLOUD'], threaded=True)
examples.add('time', 'show current time (of a user)', 'time test')

def handle_timezone(bot, ievent):
    """ <timezone> (integer) .. set users timezone in the userstate. """
    username = ievent.userhost
    if not ievent.rest:
        ievent.missing('<timezone> (integer)')
        return

    if username:
        userstate = UserState(username)
        if ievent.rest:
            try:
                timezone = int(ievent.rest)
                
                set_timezone(bot, ievent, userstate, timezone)
            except ValueError:
                ievent.reply('TZ needs to be an integer')
                return
        else:
            ievent.reply("can't determine timezone")

cmnds.add('timezone', handle_timezone, ['USER'], threaded=True)
examples.add('timezone', 'set current timezone', 'timezone +1')

def handle_ask_timezone(bot, ievent):
    """ ask for a users timezone. """
    ievent.reply('what is your timezone ? for example -1 or +4')
    response = waitforuser(bot, ievent.userhost)

    if response:
        return response.txt
    else:
        ievent.reply("can't determine timezone .. not setting it")
        return

def set_timezone(bot, ievent, userstate, timezone):
    """ set a users timezone. """
    # check for timezone validity and return False, if necessary
    try:
        tz = int(timezone)
    except ValueError:
        ievent.reply('timezone needs to be an integer')
        return False

    userstate['TZ'] = tz
    userstate.save()
    ievent.reply("timezone set to %s" % tz)
    return True

def get_time(zone, username, authuser):
    """ get the time of a user. """
    try:
        zone = int(zone)
    except ValueError:
        zone = 0

    return time.ctime(time.time() + int(time.timezone) + zone*3600)
