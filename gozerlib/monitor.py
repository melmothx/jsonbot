# gozerbot/monitor.py
#
#

""" `gozerbot.monitor` .. monitor the bots output

This module contains the Monitor base class use to implement callbacks for 
the bot's output. Used in logging plugins. The actual monitor objects live
irc and xmpp submodules.

"""

__copyright__ = 'this file is in the public domain'

## IMPORT SECTION

# gozerlib imports

from gozerlib.config import cfg as config
from utils.exception import handle_exception
from utils.trace import calledfrom
from config import cfg as config
from threadloop import ThreadLoop
from runner import cbrunners
import threads as thr

## basic imports

import Queue
import sys

class Monitor(ThreadLoop):

    """ monitor base class. used as base class for jabber and irc 
        output monitoting.

        :param name: name of the monitor
        :type name: string

    """

    def __init__(self, name="monitor"):
        ThreadLoop.__init__(self, name)        
        self.outs = []

    def add(self, name, callback, pre, threaded=False):

        """ add a monitoring callback.

            :param name: name of the plugin using this monitor callback
            :type name: string
            :param callback: the callback to fire
            :type callback: function
            :param pre: precondition (function) to check if callback should fire
            :type pre: function
            :param threaded: whether callback should be called in its own thread
            :type threaded: boolean
            :rtype: boolean

            .. literalinclude:: ../../gozerbot/monitor.py
                :pyobject: Monitor.add

        """

        name = name or calledfrom(sys._getframe(0))

        if config['loadlist'] and name not in config['loadlist']:
            return False

        self.outs.append([name, callback, pre, threaded, False])
        logging.debug('irc - added monitor %s (%s)' % (name, str(callback)))
        return True

    def disable(self, name):
        name = name.lower()

        for i in range(len(self.outs)-1, -1, -1):
            if self.outs[i][0] == name:
                self.outs[i][4] = False

    def activate(self, name):
        name = name.lower()

        for i in range(len(self.outs)-1, -1, -1):
            if self.outs[i][0] == name:
                self.outs[i][4] = True
        
    def unload(self, name):

        """ delete monitor callback. 

            :param name: name of the plugin which monitors need to be unloaded
            :type name: string
            :rtype: integer .. number of monitors removed

            .. literalinclude:: ../../gozerbot/monitor.py
                :pyobject: Monitor.unload

        """

        name = name.lower()
        nr = 0

        for i in range(len(self.outs)-1, -1, -1):
            if self.outs[i][0] == name:
                del self.outs[i]
                nr += 1

        return nr
   
    def handle(self, *args, **kwargs):

        """ check if monitor callbacks need to be fired. 

           :param args: arguments passed to the callback
           :type args: list
           :param kwargs: quoted arguments passed to the callback
           :type kwargs: dict
           :rtype: number of callbacks called 

           .. literalinclude:: ../../gozerbot/monitor.py
               :pyobject: Monitor.handle

        """

        nr = 0
        for i in self.outs:

            if not i[4]:
                continue
            # check if precondition is met
            try:
                if i[2]:
                    doit = i[2](*args, **kwargs)
                else:
                    doit = 1

            except Exception, ex:
                handle_exception()
                doit = 0

            if doit:
                # run monitor callback in its own thread

                if not i[3]:
                    cbrunners[5].put("monitor-%s" % i[0], i[1], *args)
                else:
                    thr.start_new_thread(i[1], args, kwargs)

                nr += 1

        return nr

