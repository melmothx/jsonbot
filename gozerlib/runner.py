# gozerlib/runner.py
#
#

""" threads management to run jobs. """

__copyright__ = 'this file is in the public domain'

## gozerlib imports

from gozerlib.threads import getname, start_new_thread, start_bot_command
from gozerlib.utils.exception import handle_exception
from gozerlib.utils.locking import lockdec
from gozerlib.threadloop import RunnerLoop
from gozerlib.periodical import minutely

## basic imports

import Queue
import time
import thread
import random
import logging

## define

runlock = thread.allocate_lock()
locked = lockdec(runlock)

## Runner class

class Runner(RunnerLoop):

    """
        a runner is a thread with a queue on which jobs can be pushed. 
        jobs scheduled should not take too long since only one job can 
        be executed in a Runner at the same time.

        :param name: name of the runner
        :type name: string

    """

    def __init__(self, name="runner"):
        RunnerLoop.__init__(self, name)
        self.working = False
        self.starttime = time.time()
        self.elapsed = self.starttime
        self.finished = time.time()

    def handle(self, descr, func, *args, **kwargs):

        """
            schedule a job.

            :param descr: description of the job
            :type descr: string
            :param func: function to call 
            :type func: function 

        """

        self.working = True

        try:
            name = getname(str(func))
            logging.debug('runner - running %s: %s' % (descr, name))
            self.starttime = time.time()
            func(*args, **kwargs)
            self.finished = time.time()
            self.elapsed = self.finished - self.starttime

            if self.elapsed > 3:
                logging.debug('runner - ALERT %s %s job taking too long: %s seconds' % (descr, str(func), self.elapsed))

        except Exception, ex:
            handle_exception()

        self.working = False

## CommandRunner class

class BotEventRunner(Runner):

    def handle(self, descr, func, bot, ievent, *args, **kwargs):

        """
            schedule a bot command.

            :param descr: description of the job
            :type descr: string
            :param func: function to call 
            :type func: function 
            :param bot: bot on which the command is called
            :type bot: gozerbot.botbase.BotBase
            :param ievent: event that triggered this command
            :type ievent: gozerbot.eventbase.EventBase

        """

        self.working = True

        try:
            name = getname(str(func))
            logging.debug('runner - %s (%s) running %s: %s at speed %s' % (ievent.nick, ievent.userhost, descr, str(func), ievent.speed))
            self.starttime = time.time()
            if ievent.threaded:
                args.insert(0, ievent)
                args.insert(0, bot)
                start_bot_command(func, args, kwargs)
            else:
                func(bot, ievent, *args, **kwargs)

            if ievent.closequeue and ievent.queues:
                logging.warn("closing %s queues" % len(ievent.queues))
                for queue in ievent.queues:
                    queue.put_nowait(None)
            ievent.outqueue.put_nowait(None)
            self.finished = time.time()
            self.elapsed = self.finished - self.starttime

            if self.elapsed > 3:
                logging.debug('runner - ALERT %s %s job taking too long: %s seconds' % (descr, str(func), self.elapsed))

        except Exception, ex:
            handle_exception(ievent)

        self.working = False

## Runners class

class Runners(object):

    """
        runners is a collection of runner objects.

        :param max: maximum of runners
        :type max: integer
        :param runnertype: Runner class to instatiate runners with
        :type runnertype: Runner

    """

    def __init__(self, max=100, runnertype=Runner):
        self.max = max
        self.runners = []
        self.cleanup()
        self.runnertype=runnertype

    def runnersizes(self):

        """
            return sizes of runner objects.

            :rtype: list .. list of runner queue sizes

        """

        result = []

        for runner in self.runners:
            result.append(runner.queue.qsize())

        return result

    def stop(self):

        """
            stop runners.

        """

        for runner in self.runners:
            runner.stop()

        self.cleanup()

    def start(self):

        """
            overload this if needed.
 
        """

        pass
 
    def put(self, *data):

        """
            put a job on a free runner.

        """

        for runner in self.runners:
            if not runner.working:
                runner.put(*data)
                return

        runner = self.makenew()
        runner.put(*data)
         
    def running(self):

        """
            return list of running jobs.

            :rtype: list

        """

        result = []

        for runner in self.runners:
            if runner.working:
                result.append(runner.nowrunning)

        return result

    def makenew(self):

        """
            create a new runner.

            :rtype: Runner or None

        """

        runner = None

        if len(self.runners) < self.max:
            runner = self.runnertype()
            runner.start()
            self.runners.append(runner)

        else:
            runner = random.choice(self.runners)

        return runner

    def cleanup(self):

        """
            clean up idle runners.

        """

        for runner in self.runners:
            if not runner.working:
                runner.stop() 
                self.runners.remove(runner)

# start all runners
def runners_start():
    for runner in cbrunners:
        runner.start()
    for runner in cmndrunners:
        runner.start()

# stop all runners
def runners_stop():
    for runner in cbrunners:
        runner.stop()
    for runner in cmndrunners:
        runner.stop()

## defines

# callback runners
#cbrunners = [Runners(12-i, BotEventRunner) for i in range(10)]

# command runners
#cmndrunners = [Runners(20-i, BotEventRunner) for i in range(10)]

# sweep over all runners 
#@minutely
#def cleanall():
#    for runners in cbrunners + cmndrunners:
#        runners.cleanup()

#cleanall()

defaultrunner = BotEventRunner()
