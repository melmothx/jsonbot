# gozerlib/plugins.py
#
#

""" holds all the plugins. plugins are imported modules. """

## lib imports

from commands import cmnds
from eventbase import EventBase
from persist import Persist
from utils.lazydict import LazyDict
from utils.exception import handle_exception
from admin import cmndtable
from errors import NoSuchPlugin
from jsbimport import force_import, _import

## basic imports

import os
import logging
import Queue
import copy
import sys
import logging

## defines

cpy = copy.deepcopy

## classes

class Plugins(LazyDict):

    """ the plugins object contains all the plugins. """

    def loadall(self, paths, default=[], force=False):
        """
            load all plugins from given paths, if force is true .. 
            otherwise load all plugins for default_plugins list.

        """
        imp = None
        for module in paths:
            try:
                imp = _import(module)
            except ImportError:
                logging.warn("no %s plugin package found" % module)
                continue
            logging.warn("plugins - got plugin package %s" % str(imp))
            try:
                for plug in imp.__plugs__:
                    try:
                        self.load("%s.%s" % (module,plug))
                    except KeyError:
                        logging.warn("failed to load plugin package %s" % module)
            except AttributeError:
                logging.warn("no plugins in %s" % mod)

    def unload(self, modname):
        """ unload plugin .. remove related commands from cmnds object. """
        logging.debug("plugins - unloading %s" % modname)

        try:
            cmnds.unload(modname)
        except KeyError:
            return False

        try:
            self[modname].shutdown()
            logging.debug('plugins - called %s shutdown' % modname)
        except (AttributeError, KeyError):
            pass

        return True

    def load(self, modname, replace=False):
        """ load a plugin. """

        if not replace:
            if modname in sys.modules:
                logging.debug("plugins - %s is already loaded" % modname)
                return

        logging.info("plugins - loading %s" % modname)
        try:
            mod = _import(modname)
        except ImportError, ex:
            logging.error("can't import %s - %s" % (modname, str(ex)))
            return
        try:
            self[modname] = mod
        except KeyError:
            logging.error("plugins - failed to load %s" % modname)
            raise NoSuchPlugin(modname)

        try:
            init = getattr(self[modname], 'init')
        except AttributeError:
            return self[modname]

        init()
        logging.debug('plugins - %s init called' % modname)

        return self[modname]

    def reload(self, modname):
        """ reload a plugin. just load for now. """ 
        #self.unload(modname)
        return self.load(modname, replace=True)

    def dispatch(self, bot, event, *args, **kwargs):
        """ dispatch event onto the cmnds object. check for pipelines first. """
        result = []

        if event.txt and not ' | ' in event.txt:
            self.needreloadcheck(bot, event)
            result = cmnds.dispatch(bot, event, *args, **kwargs)

            if event.queues:
                for queue in event.queues:
                    queue.put_nowait(None)

            return result

        if event.txt and ' | ' in event.txt:
            return self.pipelined(bot, event, *args, **kwargs)
              
    def pipelined(self, bot, event, *args, **kwargs):
        """ split cmnds, create events for them, chain the queues and dispatch.  """
        origqueues = event.queues
        event.queues = []
        event.allowqueue = True
        events = []

        # split commands
        for item in event.txt.split(' | '):
            e = copy.deepcopy(event)
            e.queues = []
            e.onlyqueues = True
            e.txt = item.strip()
            e.usercmnd = e.txt.split()[0]
            logging.debug('creating event for %s' % e.txt)
            e.bot = bot
            e.makeargs()
            events.append(e)

        # loop over events .. chain queues
        prevq = None

        for e in events[:-1]:
            q = Queue.Queue()
            e.queues.append(q)
            if prevq:
                e.inqueue = prevq
            prevq = q

        events[-1].inqueue = prevq
        events[-1].onlyqueues = False

        if origqueues:
            events[-1].queues = origqueues

        # do the dispatch
        for e in events:
            self.dispatch(bot, e)

        return events[-1].result

    def needreloadcheck(self, bot, event, target=None):

        """
            check if event requires a plugin to be reloaded. if so 
            reload the plugin.

        """
        logging.debug("plugins - checking for reload of %s (%s)" % (event.usercmnd, event.userhost))
        plugloaded = None

        try:
            from boot import getcmndtable
            plugin = getcmndtable()[event.usercmnd]
        except KeyError:
            logging.warn("can't find plugin to reload for %s" % event.usercmnd)
            return

        #logging.warn('cmnd: %s plugin: %s' % (event.usercmnd, plugin))

        if plugin in self:
            return False

        plugloaded = self.reload(plugin)
        logging.warn("plugins - loaded %s on demand (%s)" % (plugin, event.usercmnd))
        return plugloaded

## define

plugs = Plugins()
