# gozerlib/commands.py
#
#

""" commands are the first word. """

## lib imports

from utils.xmpp import stripped
from utils.trace import calledfrom, whichmodule
from utils.exception import handle_exception
from utils.lazydict import LazyDict
from errors import NoSuchCommand

## basic imports

import logging
import sys
import types

## classes

class Command(LazyDict):

    """  a command object. """

    def __init__(self, modname, cmnd, func, perms=[]):
        LazyDict.__init__(self)
        self.modname = modname
        self.plugname = self.modname.split('.')[-1]
        self.cmnd = cmnd
        self.func = func
        if type(perms) == types.StringType:
            perms = [perms, ]
        self.perms = perms
        self.plugin = self.plugname

class Commands(LazyDict):

    """ the commands object holds all commands of the bot. """

    def add(self, cmnd, func, perms, threaded=False, *args, **kwargs):
        """ add a command. """
        modname = calledfrom(sys._getframe())
        self[cmnd] = Command(modname, cmnd, func, perms)
        return self

    def dispatch(self, bot, event):
        """ dispatch an event if cmnd exists and user is allowed to exec this command. """
        cmnd = event.usercmnd
        try:
            c = self[cmnd]
        except KeyError: 
            raise NoSuchCommand(cmnd)

        id = event.auth or event.userhost

        ## core business

        if bot.allowall:
            return self.doit(bot, event, c)
        elif not bot.users or bot.users.allowed(id, c.perms, bot=bot):
            return self.doit(bot, event, c)
        elif bot.cfg and bot.cfg.auto_register:
            bot.users.addguest(event.userhost)
            if bot.users.allowed(id, c.perms, bot=bot):
                return self.doit(bot, event, c)
        return []

    def doit(self, bot, event, target):
        id = event.auth or event.userhost
        logging.warn('dispatching %s for %s' % (event.usercmnd, id))
        result = []
        try:
            target.func(bot, event)
            result = event.result
        except Exception, ex:
            logging.error('commands - %s - error executing %s' % (whichmodule(), str(target.func)))
            handle_exception(event)

        if event.queues:
            for queue in event.queues:
                queue.put_nowait(None)
        return result

    def unload(self, modname):
        """ remove modname registered commands from store. """
        delete = []

        for name, cmnd in self.iteritems():
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
