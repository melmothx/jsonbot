# gozerlib/plugins.py
#
#

""" holds all the plugins. plugins are imported modules. """

## gozerlib imports

from commands import cmnds
from callbacks import callbacks, remote_callbacks, first_callbacks, last_callbacks
from eventbase import EventBase
from persist import Persist
from utils.lazydict import LazyDict
from utils.exception import handle_exception
from boot import cmndtable, plugin_packages
from errors import NoSuchPlugin
from utils.locking import locked
from jsbimport import force_import, _import

## basic imports

import os
import logging
import Queue
import copy
import sys

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
                handle_exception()
                logging.warn("plugins - no %s plugin package found" % module)
                continue
            except Exception, ex:
                handle_exception()
            logging.debug("plugins - got plugin package %s" % module)
            try:
                for plug in imp.__plugs__:
                    try:
                        self.reload("%s.%s" % (module,plug))
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
            self[modname].shutdown()
            logging.debug('plugins - called %s shutdown' % modname)
        except KeyError:
            logging.debug("plugins - no %s module found" % modname) 
            return False
        except AttributeError:
            pass

        try:
            cmnds.unload(modname)
        except KeyError:
            return False

        try:
            first_callbacks.unload(modname)
        except KeyError:
            return False

        try:
            callbacks.unload(modname)
        except KeyError:
            return False

        try:
            last_callbacks.unload(modname)
        except KeyError:
            return False

        try:
            remote_callbacks.unload(modname)
        except KeyError:
            return False

        return True

    def load(self, modname, force=False):
        """ load a plugin. """
        if self.has_key(modname):
            try:
                logging.info("plugins - %s already loaded" % modname)                
                self[modname] = reload(self[modname])
                try:
                    init = getattr(self[modname], 'init')
                except AttributeError:
                    logging.info("%s reloaded - no init" % modname)
                    return self[modname]

                init()
                logging.debug('plugins - %s init called' % modname)
                logging.info("%s reloaded - with init" % modname)
                return self[modname]
            except Exception, ex:
                handle_exception()
                
        logging.debug("plugins - trying %s" % modname)
        try:
            mod = _import(modname)
        except ImportError, ex:
            logging.warn("plugins - import error on %s - %s" % (modname, str(ex)))
            raise NoSuchPlugin(modname)
        try:
            self[modname] = mod
        except KeyError:
            logging.error("plugins - failed to load %s" % modname)
            raise NoSuchPlugin(modname)

        try:
            init = getattr(self[modname], 'init')
        except AttributeError:
            logging.info("%s loaded - no init" % modname)
            return self[modname]

        try:
            init()
            logging.debug('plugins - %s init called' % modname)
        except Exception, ex:
            handle_exception()
        logging.info("%s loaded - with init" % modname)
        return self[modname]

    def reload(self, modname, force=True):
        """ reload a plugin. just load for now. """ 
        if self.has_key(modname):
            self.unload(modname)
        try:
            return self.load(modname, force=force)
        except ImportError, ex:
            logging.warn("plugiins - %s not found - %s" % (modname, str(ex)))

    def dispatch(self, bot, event, wait=0, *args, **kwargs):
        """ dispatch event onto the cmnds object. check for pipelines first. """
        result = []
        if event.txt and not ' | ' in event.txt:
            self.reloadcheck(bot, event)
            return cmnds.dispatch(bot, event, wait=wait, *args, **kwargs)

        if event.txt and ' | ' in event.txt:
            return self.pipelined(bot, event, wait=wait, *args, **kwargs)

        return event              

    def pipelined(self, bot, event, wait=0, *args, **kwargs):
        """ split cmnds, create events for them, chain the queues and dispatch.  """
        origqueues = event.queues
        event.queues = []
        event.allowqueue = True
        event.closequeue = True
        events = []

        # split commands
        for item in event.txt.split(' | '):
            e = cpy(event)
            e.queues = []
            e.onlyqueues = True
            e.txt = item.strip()
            e.usercmnd = e.txt.split()[0].lower()
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
            self.dispatch(bot, e, wait=wait)

        return events[-1]

    def reloadcheck(self, bot, event, target=None):
        """
            check if event requires a plugin to be reloaded. if so 
            reload the plugin.

        """
        logging.warn("plugins - checking for reload of %s (%s)" % (event.usercmnd, event.userhost))
        plugloaded = None

        try:
            from boot import getcmndtable
            plugin = getcmndtable()[event.usercmnd.lower()]
        except KeyError:
            logging.debug("plugins - can't find plugin to reload for %s" % event.usercmnd)
            return

        #logging.warn('cmnd: %s plugin: %s' % (event.usercmnd, plugin))

        if plugin in self:
            logging.warn("plugins - %s already loaded" % plugin)
            return False

        logging.debug("plugins - loaded %s on demand (%s)" % (plugin, event.usercmnd))
        plugloaded = self.reload(plugin)
        return plugloaded

## define

plugs = Plugins()
