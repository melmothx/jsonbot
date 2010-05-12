# gozerlib/commands.py
#
#

""" 
    the commands module provides the infrastructure to dispatch commands. 
    commands are the first word of a line. 

"""

## gozerlib imports

from threads import start_new_thread, start_bot_command
from utils.xmpp import stripped
from utils.trace import calledfrom, whichmodule
from utils.exception import handle_exception
from utils.lazydict import LazyDict
from errors import NoSuchCommand
from config import cfg as mainconfig

## basic imports

import logging
import sys
import types

## classes

class Command(LazyDict):

    """
        a command object. 

        :param modname: the module name in which this command is registered
        :type modname: string
        :param cmnd: the command to dispatch
        :type cmnd: string
        :param func: the function handling the command
        :type func: function
        :param perms: permissions needed to execute the command
        :type perms: list of strings

    """

    def __init__(self, modname, cmnd, func, perms=[], threaded=False):
        LazyDict.__init__(self)
        self.modname = modname
        self.plugname = self.modname.split('.')[-1]
        self.cmnd = cmnd
        self.func = func
        if type(perms) == types.StringType:
            perms = [perms, ]
        self.perms = perms
        self.plugin = self.plugname
        self.threaded = threaded

class Commands(LazyDict):

    """
        the commands object holds all commands of the bot. 
    """

    def add(self, cmnd, func, perms, threaded=False, *args, **kwargs):
        """ add a command. """
        modname = calledfrom(sys._getframe())
        self[cmnd] = Command(modname, cmnd, func, perms, threaded)
        return self

    def dispatch(self, bot, event):
        """ 
            dispatch an event if cmnd exists and user is allowed to exec this 
            command.
        """
        cmnd = event.usercmnd
        try:
            c = self[cmnd]
        except KeyError: 
            raise NoSuchCommand(cmnd)

        # identity of the caller
        id = event.auth or event.userhost

        # core business
        if bot.allowall:
            return self.doit(bot, event, c)
        elif not bot.users or bot.users.allowed(id, c.perms, bot=bot):
            return self.doit(bot, event, c)
        elif mainconfig.auto_register:
            bot.users.addguest(event.userhost)
            if bot.users.allowed(id, c.perms, bot=bot):
                return self.doit(bot, event, c)
        return event

    def doit(self, bot, event, target):
        """ do the dispatching. """
        id = event.auth or event.userhost
        logging.info('commands - dispatching %s for %s' % (event.usercmnd, id))
        result = []
        try:
            if target.threaded and not bot.isgae:
                start_bot_command(target.func, (bot, event))
            else:
                target.func(bot, event)
            result = event
        except Exception, ex:
            logging.error('commands - %s - error executing %s' % (whichmodule(), str(target.func)))
            raise
        if event.queues:
            for queue in event.queues:
                queue.put_nowait(None)
        return result

    def unload(self, modname):
        """ remove modname registered commands from store. """
        delete = []
        for name, cmnd in self.iteritems():
            if not cmnd:
                continue
            if cmnd.modname == modname:
                delete.append(cmnd)

        for cmnd in delete:
            del cmnd

        return self

    def apropos(self, search):
        """ search existing commands for search term. """
        result = []
        for name, cmnd in self.iteritems():
            if search in name:
                result.append(name)

        return result

    def perms(self, cmnd):
        """ show what permissions are needed to execute cmnd. """
        try:
            return self[cmnd].perms
        except KeyError:
            return []

    def whereis(self, cmnd):
        """ return plugin name in which command is implemented. """
        try:
            return self[cmnd].plugname
        except KeyError:
            return ""

    def gethelp(self, cmnd):
        """ get the docstring of a command. used for help. """
        try:
            return self[cmnd].func.__doc__
        except KeyError:
            return

## defines

cmnds = Commands()
