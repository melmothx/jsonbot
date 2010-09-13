# gozerlib/plugs/misc.py
#
#

""" misc commands. """

## gozerbot imports

from gozerlib.utils.exception import handle_exception
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.persiststate import UserState
from gozerlib.socklib.utils.generic import waitforuser

## basic imports

import time
import os
import threading
import thread
import copy

cpy = copy.deepcopy

def handle_test(bot, ievent):
    """ give test response. """
    ievent.reply("%s - %s - it works!" % (ievent.auth or ievent.userhost, ievent.user.data.name))
    
cmnds.add('test', handle_test, ['USER', 'GUEST', ])
examples.add('test', 'give test response',' test')

def handle_testevent(bot, ievent):
    """ give dump of event. """
    ievent.reply(ievent.dump())
    
cmnds.add('test-event', handle_testevent, ['USER', 'GUEST', ])
examples.add('test-event', 'dump the event',' test-event')

def handle_source(bot, ievent):
    """ show where to fetch the bot source. """ 
    ievent.reply('see http://jsonbot.googlecode.com')

cmnds.add('source', handle_source, ['USER', 'GUEST'])
examples.add('source', 'show source url', 'source')

def handle_time(bot, ievent):
    """ show current time """
    ievent.reply("time is %s" % time.ctime(time.time()))

cmnds.add('time', handle_time, ['USER', 'GUEST'])
examples.add('time', 'show current time', 'time')
