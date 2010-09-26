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
from runner import cmndrunner

## basic imports

import logging
import sys
import types

## Command class

class Command(LazyDict):

    """ a command object. """

    def __init__(self, modname, cmnd, func, perms=[], threaded=False, wait=False, orig=None):
        LazyDict.__init__(self)
        if not modname: raise Exception("modname is not set - %s" % cmnd)
        self.modname = modname
        self.plugname = self.modname.split('.')[-1]
        self.cmnd = cmnd
        self.orig = orig
        self.func = func
        if type(perms) == types.StringType: perms = [perms, ]
        self.perms = perms
        self.plugin = self.plugname
        self.threaded = threaded
        self.wait = wait

class Commands(LazyDict):

    """
        the commands object holds all commands of the bot.
 
    """

    def add(self, cmnd, func, perms, threaded=False, wait=False, *args, **kwargs):
        """ add a command. """
        modname = calledfrom(sys._getframe())
        self[cmnd] = Command(modname, cmnd, func, perms, threaded, wait)
        try:
            c = cmnd.split('-')[1]
            if not self.subs: self.subs = LazyDict()
            if self.subs.has_key(c):
                if not self.subs[c]: self.subs[c] = []
                self.subs[c].append(Command(modname, c, func, perms, threaded, wait, cmnd))
            else: self.subs[c] = [Command(modname, c, func, perms, threaded, wait, cmnd), ]
        except IndexError: pass
        return self

    def dispatch(self, bot, event, wait=0):
        """ 
            dispatch an event if cmnd exists and user is allowed to exec this 
            command.

        """

        if event.groupchat: id = event.auth = event.userhost
        else: id = event.auth
        if mainconfig.auto_register: bot.users.addguest(id)
        #if event.usercmnd:
        #    logging.debug("setting user to %s" % id)
        if not event.user:
            event.user = bot.users.getuser(id)
            if event.user: event.userstate = UserState(event.user.data.name)
            else: logging.debug("failed to set user %s" % id)
        cmnd = event.usercmnd.lower()
        try:
            cmnd = event.chan.data.aliases[cmnd]
            event.txt = event.chan.data.cc + cmnd +  ' ' + ' '.join(event.txt.split()[1:])
            event.usercmnd = cmnd.split()[0]
            event.prepare()
        except (TypeError, KeyError, AttributeError): pass
        target = bot.plugs
        if target: target.reloadcheck(bot, event)
        try:
            c = self[event.usercmnd]
        except KeyError:
            if self.subs and self.subs.has_key(cmnd):
                if len(self.subs[cmnd]) == 1: c = self.subs[cmnd][0]
                else:
                    event.reply("use one of ", [c.orig for c in self.subs[cmnd]])
                    return
            else:
                raise NoSuchCommand(cmnd)


        # core business
        if bot.allowall: return self.doit(bot, event, c, wait=wait)
        elif not bot.users or bot.users.allowed(id, c.perms, bot=bot): return self.doit(bot, event, c, wait=wait)
        elif bot.users.allowed(id, c.perms, bot=bot): return self.doit(bot, event, c, wait=wait)
        return event

    def doit(self, bot, event, target, wait=0):
        """ do the dispatching. """
        id = event.auth or event.userhost
        event.iscmnd = True
        logging.warning('commands - dispatching %s for %s' % (event.usercmnd, id))
        try:
            if bot.isgae or wait:
                target.func(bot, event)
                if event.closequeue and event.queues:
                    for q in event.queues:
                        q.put_nowait(None)
                    event.outqueue.put_nowait(None)
            else:
                if target.threaded:
                    logging.warning("commands - launching thread for %s" % event.usercmnd)
                    thread = start_bot_command(target.func, (bot, event))
                    if bot.isgae and event.closequeue:
                        if event.queues:
                            for q in event.queues: q.put_nowait(None)
                        event.outqueue.put_nowait(None)
                else: cmndrunner.put(target.modname, target.func, bot, event)
        except Exception, ex:
            logging.error('commands - %s - error executing %s' % (whichmodule(), str(target.func)))
            raise
        return event

    def unload(self, modname):
        """ remove modname registered commands from store. """
        delete = []
        for name, cmnd in self.iteritems():
            if not cmnd: continue
            if cmnd.modname == modname: delete.append(cmnd)
        for cmnd in delete: del cmnd
        return self

    def apropos(self, search):
        """ search existing commands for search term. """
        result = []
        for name, cmnd in self.iteritems():
            if search in name: result.append(name)
        return result

    def perms(self, cmnd):
        """ show what permissions are needed to execute cmnd. """
        try: return self[cmnd].perms
        except KeyError: return []

    def whereis(self, cmnd):
        """ return plugin name in which command is implemented. """
        try: return self[cmnd].plugname
        except KeyError: return ""

    def gethelp(self, cmnd):
        """ get the docstring of a command. used for help. """
        try: return self[cmnd].func.__doc__
        except KeyError: pass

## global commands

cmnds = Commands()
