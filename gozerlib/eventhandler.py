# gozerlib/eventhandler.py
#
#

""" event handler. use to dispatch function in main loop. """

## gozerlib imports

from utils.exception import handle_exception
from utils.locking import lockdec
from threads import start_new_thread

## basic imports

import Queue
import thread

## locks

handlerlock = thread.allocate_lock()
locked = lockdec(handlerlock)

## classes

class Eventhandler(object):

    """
        events are handled in 11 queues with different priorities:
        queue0 is tried first queue10 last.

    """

    def __init__(self):
        self.sortedlist = []
        self.queues = {}

        for i in range(11):
            self.queues[i] = Queue.Queue()
            self.sortedlist.append(i)

        self.sortedlist.sort()
        self.go = Queue.Queue()
        self.stopped = False
        self.running = False
        self.nooutput = False

    def start(self):
        """ start the eventhandler thread. """

        self.stopped = False

        if not self.running:
            start_new_thread(self.handleloop, ())
            self.running = True

    def stop(self):
        """ stop the eventhandler thread. """
        self.running = False
        self.stopped = True
        self.go.put('Yihaaa')

    def put(self, speed, func, *args, **kwargs):
        """ put item on the queue. """
        self.queues[10-speed].put_nowait((func, args, kwargs))
        self.go.put('go')

    def getready(self):
        """ check queues from available functions to execute. """
        ready = []
        for i in self.sortedlist:
            if self.queues[i].qsize():
                ready.append(i)
                break

        return ready

    def handle_one(self):
        """ do 1 loop over ready queues. """
        ready = self.getready()
        for i in ready:
            self.dispatch(self.queues[i])

    def handleloop(self):
        """ thread that polls the queues for items to dispatch. """
        logging.debug('eventhandler - starting handle thread')
        while not self.stopped:
            self.go.get()
            self.handle_one()

        logging.debug('eventhandler - stopping %s' % str(self))

    def dispatch(self, queue):
        """ dispatch functions from provided queue. """
        try:
            todo = queue.get_nowait()
        except Queue.Empty:
            return

        try:
            (func, args, kwargs) = todo
            func(*args, **kwargs)
        except ValueError:
            try:
                (func, args) = todo
                func(*args)
            except ValueError:
                (func, ) = todo
                func()

        except:
            handle_exception()

## defines

# handler to use in main prog
mainhandler = Eventhandler()
