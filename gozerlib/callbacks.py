# gozerlib/callbacks.py
#
#

""" 
    bot callbacks .. callbacks occure on registered events. a precondition 
    function can optionaly be provided to see if the callback should fire. 

"""

## gozerlib imports

from threads import getname 
from utils.exception import handle_exception
from utils.trace import calledfrom, whichplugin
from utils.dol import Dol
from plugins import plugs

## basic imports

import sys
import copy
import thread
import logging

## classes

class Callback(object):

    """ 
        class representing a callback.

        :param func: function to execute
        :param prereq: prerequisite function 
        :param plugname: plugin to register this callback with 
        :param kwargs: dict to pass on to the callback 
        :param threaded: whether the callback should be executed in its own thread
        :param speed: determines which runnerspool to run this callback on

    """

    def __init__(self, func, prereq, plugname, kwargs, threaded=False, \
speed=5):
        self.func = func # the callback function
        self.prereq = prereq # pre condition function
        self.plugname = plugname # plugin name
        self.kwargs = kwargs # kwargs to pass on to function
        self.threaded = copy.deepcopy(threaded) # run callback in thread
        self.speed = copy.deepcopy(speed) # speed to execute callback with
        self.activate = False

class Callbacks(object):

    """ 
        dict of lists containing callbacks.  Callbacks object take care of 
        dispatching the callbacks based on incoming events. see Callbacks.check()

    """

    def __init__(self):

        # self.cbs holds the dict of list. entry value is the event (string)
        self.cbs = Dol()

    def size(self):

        """ return number of callbacks. """

        return len(self.cbs)

    def add(self, what, func, prereq=None, kwargs=None, threaded=False, nr=False, speed=5):

        """ 
            add a callback. 

            :param what: event to fire callback for
            :param func: function to execute
            :param prereq: prerequisite function 
            :param plugname: plugin to register this callback with 
            :param kwargs: dict to pass on to the callback 
            :param threaded: whether the callback should be executed in its own thread
            :param speed: determines which runnerspool to run this callback on

        """

        what = what.upper()

        # get the plugin this callback was registered from
        #plugname = calledfrom(sys._getframe(0))
        plugname = whichplugin()

        # see if kwargs is set if not init to {}
        if not kwargs:
            kwargs = {}

        # add callback to the dict of lists
        if nr != False:
            self.cbs.insert(nr, what, Callback(func, prereq, plugname, kwargs, threaded, speed))
        else:
            self.cbs.add(what, Callback(func, prereq, plugname, kwargs, threaded, speed))

        logging.debug('callbacks - added %s (%s)' % (what, plugname))

    def unload(self, plugname):

        """ unload all callbacks registered in a plugin. """

        unload = []

        # look for all callbacks in a plugin
        for name, cblist in self.cbs.iteritems():
            index = 0
            for item in cblist:
                if item.plugname == plugname:
                    unload.append((name, index))
                index += 1

        # delete callbacks
        for callback in unload[::-1]:
            self.cbs.delete(callback[0], callback[1])
            logging.debug('callbacks - unloaded %s' % callback[0])

    def disable(self, plugname):

        """ disable all callbacks registered in a plugin. """

        unload = []

        # look for all callbacks in a plugin
        for name, cblist in self.cbs.iteritems():
            index = 0
            for item in cblist:
                if item.plugname == plugname:
                    item.activate = False

    def activate(self, plugname):

        """ activate all callbacks registered in a plugin. """

        unload = []

        # look for all callbacks in a plugin
        for name, cblist in self.cbs.iteritems():
            index = 0
            for item in cblist:
                if item.plugname == plugname:
                    item.activate = True

    def whereis(self, cmnd):

        """ show where ircevent.CMND callbacks are registered """

        result = []
        cmnd = cmnd.upper()

        # locate callbacks for CMND
        for c, callback in self.cbs.iteritems():
            if c == cmnd:
                for item in callback:
                    if not item.plugname in result:
                        result.append(item.plugname)

        return result

    def list(self):

        """ show all callbacks. """

        result = []

        # loop over callbacks and collect callback functions
        for cmnd, callbacks in self.cbs.iteritems():
            for cb in callbacks:
                result.append(getname(cb.func))

        return result

    def check(self, bot, event):

        """ 
            check for callbacks to be fired. 

            :param bot: bot where event originates from
            :param event: event that needs to be checked

            .. literalinclude:: ../../gozerlib/callbacks.py
                :pyobject: Callbacks.check

        """

        # check for "ALL" callbacks
        if self.cbs.has_key('ALL'):
            for cb in self.cbs['ALL']:
                self.callback(cb, bot, event)

        type = event.cbtype or event.cmnd
        self.reloadcheck(event)
        #logging.info("callbacks - %s - %s" % (event.userhost, type))
 
        # check for CMND callbacks
        if self.cbs.has_key(type):
            for cb in self.cbs[type]:
                self.callback(cb, bot, event)

    def callback(self, cb, bot, event):

        """ 
            do the actual callback with provided bot and event as arguments.

            :param cb: the callback to fire
            :param bot: bot to call the callback on
            :param event: the event that triggered the callback

            .. literalinclude:: ../../gozerlib/callbacks.py
                :pyobject: Callbacks.callback

        """

        try:
            # see if the callback pre requirement succeeds
            if cb.prereq:
                logging.debug('callbacks - excecuting in loop %s' % str(cb.prereq))
                if not cb.prereq(bot, event):
                    return

            # check if callback function is there
            if not cb.func:
                return

            logging.warning('callbacks - excecuting callback %s' % str(cb.func))

            event.iscallback = True

            # launch the callback
          
            cb.func(bot, event)
            return True

        except Exception, ex:
            handle_exception()


    def reloadcheck(self, event):
        #logging.debug("callbacks - checking for reload of %s (%s)" % (event.cmnd, event.userhost))
        plugloaded = []
        target = event.cbtype or event.cmnd

        try:
            from boot import getcallbacktable
            plugins = getcallbacktable()[target]
        except KeyError:
            #logging.warn("can't find plugin to reload for %s" % event.cmnd)
            return

        logging.info('callback: %s plugin: %s' % (target, plugins))

        for name in plugins:
            if name in plugs:
                continue
            else:
                logging.debug("on demand reloading of %s" % name)
                try:
                    plugloaded.append(plugs.reload(name))
                except Exception, ex:
                    handle_exception()

        return plugloaded


## define

callbacks = Callbacks()
gn_callbacks = Callbacks()
