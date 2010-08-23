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
        nrempty = 0
        while not self.stopped:

            try:
                data = self.queue.get_nowait()
            except Queue.Empty:
                time.sleep(0.05)
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
        self.queue.put_nowait(None)

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

            self.nowrunning = data[0]
            logging.debug('%s - now running %s' % (self.name, self.nowrunning))
            self.handle(*data)

        self.running = False
        logging.debug('%s - stopping threadloop' % self.name)

class TimedLoop(ThreadLoop):

    """ threadloop that sleeps x seconds before executing. """

    def __init__(self, name, sleepsec=300, *args, **kwargs):
        ThreadLoop.__init__(self, name, *args, **kwargs)
        self.sleepsec = sleepsec

    def _loop(self):
        logging.debug('%s - starting timedloop (%s seconds)' % (self.name, self.sleepsec))
        self.stopped = False
        self.running = True

        while not self.stopped:
            time.sleep(self.sleepsec)

            if self.stopped:
                logging.debug("%s - loop is stopped" % self.name)
                break

            logging.debug('%s - now running timedloop' % self.name)
            try:
                self.handle()
            except Exception, ex:
                handle_exception()

        self.running = False
        logging.debug('%s - stopping timedloop' % self.name)
