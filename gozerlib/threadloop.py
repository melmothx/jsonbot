# gozerlib/threadloop.py
#
#

""" class to implement start/stoppable threads. """

## lib imports
from threads import start_new_thread

## basic imports
import Queue
import time
import logging

## classes

class ThreadLoop(object):

    """ implement startable/stoppable threads. """

    def __init__(self, name="", queue=None):
        self.name = name or 'idle'
        self.stopped = False
        self.running = False
        self.outs = []
        self.queue = queue or Queue.Queue()
        self.nowrunning = "none"

    def _loop(self):
        logging.debug('%s - starting threadloop' % self.name)
        self.running = True

        while not self.stopped:

            try:
                data = self.queue.get_nowait()
            except Queue.Empty:
                if self.stopped:
                    break
                time.sleep(0.1)
                continue

            if self.stopped:
                break

            if not data:
                break
            #logging.debug('%s - running %s' % (self.name, str(data)))
            self.handle(*data)

        self.running = False
        logging.debug('%s - stopping threadloop' % self.name)

    def put(self, *data):

        """ put data on task queue. """

        self.queue.put_nowait(data)

    def start(self):

        """ start the thread. """

        if not self.running:
            start_new_thread(self._loop, ())

    def stop(self):

        """ stop the thread. """

        self.stopped = True
        self.running = False
        self.queue.put(None)

    def handle(self, *args, **kwargs):

        """ overload this. """

        pass

class RunnerLoop(ThreadLoop):

    """ dedicated threadloop for bot commands/callbacks. """


    def _loop(self):
        logging.debug('%s - starting threadloop' % self.name)
        self.running = True

        while not self.stopped:

            try:
                data = self.queue.get()
            except Queue.Empty:
                if self.stopped:
                    break
                time.sleep(0.1)
                continue

            if self.stopped:
                break

            if not data:
                break

            self.nowrunning = data[0]
            logging.debug('%s - now running %s' % (self.name, self.nowrunning))
            self.handle(*data)

        self.running = False
        self.debug('%s - stopping threadloop' % self.name)
