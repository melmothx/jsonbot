# gozerlib/plugins.py
#
#

""" holds all the plugins. plugins are imported modules. """

## gozerlib imports

from commands import cmnds
from eventbase import EventBase
from persist import Persist
from utils.lazydict import LazyDict
from utils.exception import handle_exception
from admin import cmndtable, plugin_packages
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

    def exit(self):
        for plugname in self:
            self.unload(plugname)         

    def loadall(self, paths=[], force=False):
        """
            load all plugins from given paths, if force is true .. 
            otherwise load all plugins for default_plugins list.

        """
        if not paths:
            paths = plugin_packages
        imp = None
        for module in paths:
            try:
                imp = _import(module)
            except ImportError:
                logging.warn("plugins - no %s plugin package found" % module)
                continue
            except Exception, ex:
                handle_exception()
            logging.debug("plugins - got plugin package %s" % module)
            try:
                for plug in imp.__plugs__:
                    try:
                        self.load("%s.%s" % (module,plug), force=force)
                    except KeyError:
                        logging.debug("failed to load plugin package %s" % module)
                    except Exception, ex:
                        handle_exception()
            except AttributeError:
                logging.warn("no plugins in %s .. define __plugs__ in __init__.py" % module)

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

    def load(self, modname, force=False):
        """ load a plugin. """
        if not force:
            if modname in sys.modules:
                logging.debug("plugins - %s is already loaded" % modname)
                self[modname] = sys.modules[modname]
                return sys.modules[modname]
        else:
            try:
                del sys.modules[modname]
            except KeyError:
                pass
        logging.debug("plugins - loading %s" % modname)
        mod = _import(modname)

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

    def reload(self, modname, force=False):
        """ reload a plugin. just load for now. """ 
        self.unload(modname)
        return self.load(modname, force=force)

    def dispatch(self, bot, event, *args, **kwargs):
        """ dispatch event onto the cmnds object. check for pipelines first. """
        result = []
        if event.txt and not ' | ' in event.txt:
            #self.needreloadcheck(bot, event)
            return cmnds.dispatch(bot, event, *args, **kwargs)

        if event.txt and ' | ' in event.txt:
            return self.pipelined(bot, event, *args, **kwargs)

        return event              

    def pipelined(self, bot, event, *args, **kwargs):
        """ split cmnds, create events for them, chain the queues and dispatch.  """
        origqueues = event.queues
        event.queues = []
        event.allowqueue = True
        event.closequeue = False
        events = []

        # split commands
        for item in event.txt.split(' | '):
            e = copy.deepcopy(event)
            #print e
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
        events[-1].closequeue = True

        if origqueues:
            events[-1].queues = origqueues

        # do the dispatch
        for e in events:
            self.dispatch(bot, e)

        return events[-1]

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
            logging.info("plugins - can't find plugin to reload for %s" % event.usercmnd)
            return

        #logging.warn('cmnd: %s plugin: %s' % (event.usercmnd, plugin))

        if plugin in self:
            return False

        logging.warn("plugins - loaded %s on demand (%s)" % (plugin, event.usercmnd))
        plugloaded = self.reload(plugin)
        return plugloaded

## define

plugs = Plugins()
