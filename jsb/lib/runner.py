# jsb/runner.py
#
#

""" threads management to run jobs. """

## jsb imports

from jsb.lib.threads import getname, start_new_thread, start_bot_command
from jsb.utils.exception import handle_exception
from jsb.utils.locking import locked, lockdec
from jsb.utils.lockmanager import rlockmanager, lockmanager
from jsb.utils.trace import callstack
from jsb.lib.threadloop import RunnerLoop
from jsb.lib.callbacks import callbacks

## basic imports

import Queue
import time
import thread
import random
import logging
import sys

## Runner class

class Runner(RunnerLoop):

    """
        a runner is a thread with a queue on which jobs can be pushed. 
        jobs scheduled should not take too long since only one job can 
        be executed in a Runner at the same time.

    """

    def __init__(self, name="runner"):
        RunnerLoop.__init__(self, name)
        self.working = False
        self.starttime = time.time()
        self.elapsed = self.starttime
        self.finished = time.time()

    def handle(self, descr, func, *args, **kwargs):
        """ schedule a job. """
        self.working = True
        name = getname(str(func))
        try:
            rlockmanager.acquire(getname(str(func)))
            name = getname(str(func))
            self.name = name
            logging.debug('runner - running %s: %s' % (descr, name))
            self.starttime = time.time()
            func(*args, **kwargs)
            self.finished = time.time()
            self.elapsed = self.finished - self.starttime
            if self.elapsed > 3:
                logging.debug('runner - ALERT %s %s job taking too long: %s seconds' % (descr, str(func), self.elapsed))
        except Exception, ex: handle_exception()
        finally: rlockmanager.release()
        self.working = False

## BotEventRunner class

class BotEventRunner(Runner):

    def handle(self, descr, func, bot, ievent, *args, **kwargs):
        """ schedule a bot command. """
        try:
            self.starttime = time.time()
            lockmanager.acquire(getname(str(func)))
            name = getname(str(func))
            self.name = name
            self.working = True
            logging.debug("runner - now running %s" % name)
            func(bot, ievent, *args, **kwargs)
            if ievent.closequeue and ievent.queues:
                logging.debug("closing %s queues" % len(ievent.queues))
                for queue in ievent.queues: queue.put_nowait(None)
            ievent.inqueue.put_nowait(None)
            if not ievent.dontclose: ievent.outqueue.put_nowait(None)
            self.finished = time.time()
            self.elapsed = self.finished - self.starttime
            if self.elapsed > 3:
                logging.warn('runner - ALERT %s %s job taking too long: %s seconds' % (descr, str(func), self.elapsed))
        except Exception, ex:
            if ievent.showexception: handle_exception(ievent)
            else: handle_exception(stop=True)
        finally: lockmanager.release(getname(str(func)))
        self.working = False

## Runners class

class Runners(object):

    """ runners is a collection of runner objects. """

    def __init__(self, max=100, runnertype=Runner):
        self.max = max
        self.runners = []
        self.runnertype=runnertype

    def runnersizes(self):
        """ return sizes of runner objects. """
        result = []
        for runner in self.runners: result.append(runner.queue.qsize())
        return result

    def stop(self):
        """ stop runners. """
        for runner in self.runners: runner.stop()

    def start(self):
        """ overload this if needed. """
        pass
 
    def put(self, *data):
        """ put a job on a free runner. """
        for runner in self.runners:
            if not runner.queue.qsize():
                runner.put(*data)
                return
        runner = self.makenew()
        runner.put(*data)
         
    def running(self):
        """ return list of running jobs. """
        result = []
        for runner in self.runners:
            if runner.queue.qsize(): result.append(runner.nowrunning)
        return result

    def makenew(self):
        """ create a new runner. """
        runner = None
        for i in self.runners:
            if not i.queue.qsize(): return i
        if len(self.runners) < self.max:
            runner = self.runnertype()
            runner.start()
            self.runners.append(runner)
        else: runner = random.choice(self.runners)
        return runner

    def cleanup(self):
        """ clean up idle runners. """
        if not len(self.runners): logging.info("nothing to clean")
        for index in range(len(self.runners)-1, -1, -1):
            runner = self.runners[index]
            logging.debug("runner - cleanup %s" % runner.name)
            if not runner.queue.qsize(): runner.stop() ; del self.runners[index]
            else: logging.info("runners - %s" % runner.nowrunning)
## global runners

cmndrunner = defaultrunner = longrunner = Runners(10, BotEventRunner)

def runnercleanup(bot, event):
    logging.debug("runner sizes: %s" % str(cmndrunner.runnersizes()))
    cmndrunner.cleanup()

callbacks.add("TICK", runnercleanup)