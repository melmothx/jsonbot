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
from persiststate import UserState

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

    def __init__(self, modname, cmnd, func, perms=[], threaded=False, orig=None):
        LazyDict.__init__(self)
        self.modname = modname
        self.plugname = self.modname.split('.')[-1]
        self.cmnd = cmnd
        self.orig = orig
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
        try:
            c = cmnd.split('-')[1]
            if not self.subs:
                self.subs = LazyDict()
            if self.subs.has_key(c):
                self.subs[c].append(Command(modname, c, func, perms, threaded, cmnd))
            else:
                self.subs[c] = [Command(modname, c, func, perms, threaded, cmnd), ]
        except IndexError:
            pass
        return self

    def dispatch(self, bot, event):
        """ 
            dispatch an event if cmnd exists and user is allowed to exec this 
            command.
        """
        if mainconfig.auto_register:
            bot.users.addguest(event.userhost)

        # identity of the caller
        id = event.auth or event.userhost

        if event.usercmnd:
            logging.debug("setting user to %s" % id)
            event.user = bot.users.getuser(id)
            if event.user:
                event.userstate = UserState(event.user.data.name)
            else:
                logging.debug("failed to set user %s" % id)
        cmnd = event.usercmnd
        try:
            cmnd = event.userstate.data.aliases[cmnd]
            event.usercmnd = cmnd
            event.makeargs()
        except (TypeError, KeyError, AttributeError):
            pass

        target = bot.plugs
        if target:
            target.reloadcheck(bot, event)

        try:
            c = self[cmnd]
        except KeyError:
            if self.subs and self.subs.has_key(cmnd):
                if len(self.subs[cmnd]) == 1:
                    c = self.subs[cmnd][0]
                else:
                    event.reply("use one of ", [c.orig for c in self.subs[cmnd]])
                    return
            else:
                raise NoSuchCommand(cmnd)


        # core business
        if bot.allowall:
            return self.doit(bot, event, c)
        elif not bot.users or bot.users.allowed(id, c.perms, bot=bot):
            return self.doit(bot, event, c)
        elif bot.users.allowed(id, c.perms, bot=bot):
            return self.doit(bot, event, c)
        return event

    def doit(self, bot, event, target):
        """ do the dispatching. """
        id = event.auth or event.userhost
        logging.info('commands - dispatching %s for %s' % (event.usercmnd, id))
        try:
            if target.threaded and not bot.isgae:
                start_bot_command(target.func, (bot, event))
            else:
                target.func(bot, event)
            e = event
        except Exception, ex:
            logging.error('commands - %s - error executing %s' % (whichmodule(), str(target.func)))
            raise
        e.outqueue.put_nowait(None)
        if True:
            if e.queues:
                for q in e.queues:
                    q.put_nowait(None)
        return e

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
