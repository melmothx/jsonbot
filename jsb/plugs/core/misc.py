# jsb/plugs/misc.py
#
#

""" misc commands. """

## gozerbot imports

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persiststate import UserState
from jsb.lib.socklib.utils.generic import waitforuser

## basic imports

import time
import os
import threading
import thread
import copy

## defines

cpy = copy.deepcopy

## test command

def handle_test(bot, ievent):
    """ give test response. """
    ievent.reply("%s (%s) - %s - it works!" % (ievent.auth or ievent.userhost, ievent.nick, ievent.user.data.name))
    
cmnds.add('test', handle_test, ['USER', 'GUEST'])
examples.add('test', 'give test response',' test')

## source command

def handle_source(bot, ievent):
    """ show where to fetch the bot source. """ 
    ievent.reply('see http://jsonbot.googlecode.com')

cmnds.add('source', handle_source, ['USER', 'GUEST'])
examples.add('source', 'show source url', 'source')

