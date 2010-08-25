# gozerbot/periodical.py
#
#

""" periodic pulse provider. """

__author__ = "Wijnand 'tehmaze' Modderman - http://tehmaze.com"
__license__ = "BSD License"

## gozerlib imports

from utils.exception import handle_exception
from utils.trace import calledfrom, whichmodule
from utils.locking import lockdec
from utils.timeutils import strtotime
import threads as thr

## basic imorts

import datetime
import sys
import time
import thread
import types
import logging

## locks

plock    = thread.allocate_lock()
locked   = lockdec(plock)
pidcount = 0

## classes

class JobError(Exception):

    """
        job error exception.

    """

    pass

class Job(object):

    """ job to be scheduled. """

    group = ''
    pid   = -1

    def __init__(self):
        global pidcount
        pidcount += 1
        self.pid = pidcount

    def id(self):
        """ return job id. """
        return self.pid

    def member(self, group):
        """
             check for group membership.

             :param group: group to check for
             :type group: string
             :rtype: boolean

        """
        return self.group == group

    def do(self):
        """ try the callback. """
        try:
            self.func(*self.args, **self.kw)
        except Exception, ex:
            handle_exception()

class JobAt(Job):

    """
        job to run at a specific time/interval/repeat.

        :param start: start time
        :type start: int, float or string
        :param interval: time between alarms
        :type interval: integer
        :param repeat: number of repeats
        :type interval: integer
        :param func: the function to execute
        :type func: function

    """

    def __init__(self, start, interval, repeat, func, *args, **kw):
        Job.__init__(self)
        self.func = func
        self.args = args
        self.kw = kw
        self.repeat = repeat
        self.description = ""
        self.counts = 0

        # check start time format
        if type(start) in [types.IntType, types.FloatType]:
            self.next = float(start)
        elif type(start) in [types.StringType, types.UnicodeType]:
            d = strtotime(start)
            if d and d > time.time():
                self.next = d
            else:
                raise JobError("invalid date/time")

        if type(interval) in [types.IntType]:
            d = datetime.timedelta(days=interval)
            self.delta = d.seconds
        else:
            self.delta = interval

    def __repr__(self):
        """ return a string representation of the JobAt object. """
        return '<JobAt instance next=%s, interval=%s, repeat=%d, function=%s>' % (str(self.next),
            str(self.delta), self.repeat, str(self.func))

    def check(self):
        """ run check to see if job needs to be scheduled. """
        if self.next <= time.time():
            logging.debug('periodical - running %s - %s' % (str(self.func), self.description))
            self.func(*self.args, **self.kw)
            self.next += self.delta
            self.counts += 1
            if self.repeat > 0 and self.counts >= self.repeat:
                return False # remove this job

        return True

class JobInterval(Job):

    """
        job to be scheduled at certain interval.

        :param interval: time between alarms
        :type interval: integer
        :param repeat: number of repeats
        :type interval: integer
        :param func: the function to execute
        :type func: function

    """

    def __init__(self, interval, repeat, func, *args, **kw):
        Job.__init__(self)
        self.func = func
        self.args = args
        self.kw = kw
        self.repeat = int(repeat)
        self.counts = 0
        self.interval = float(interval)
        self.description = ""
        self.next = time.time() + self.interval
        self.group = None

    def __repr__(self):
        return '<JobInterval instance next=%s, interval=%s, repeat=%d, group=%s, \
function=%s>' % (str(self.next), str(self.interval), self.repeat, self.group,
str(self.func))

    def check(self):
        """ run check to see if job needs to be scheduled. """
        if self.next <= time.time():
            logging.debug('periodical - running %s - %s' % (str(self.func), self.description))
            self.next = time.time() + self.interval
            thr.start_new_thread(self.do, ())
            self.counts += 1
            if self.repeat > 0 and self.counts >= self.repeat:
                return False # remove this job

        return True


class Periodical(object):

    """ periodical scheduler. """

    SLEEPTIME = 60 # smallest interval possible

    def __init__(self):
        self.jobs = []
        self.running = []
        self.run = False

    def start(self):
        """ start the periodical scheduler. """
        if not self.run:
            thr.start_new_thread(self.checkloop, ())

    def addjob(self, sleeptime, repeat, function, description="" , *args, **kw): 
        """
            add a periodical job.

            :param sleeptime: sleeptime between intervals
            :type sleeptime: float
            :param repeat: number of times to repeat 
            :type repeat: integer
            :param function: function to execute
            :type function: function
            :param description: description of the periodical job
            :type description: string

        """
        job = JobInterval(sleeptime, repeat, function, *args, **kw)
        job.group = calledfrom(sys._getframe())
        job.description = str(description) or whichmodule()
        self.jobs.append(job)
        logging.warn("periodical - added %s job" % str(function))
        return job.pid

    def changeinterval(self, pid, interval):
        """
             change interval of of peridical job.

             :param pid: id op the periodical job
             :type pid: integer
             :param interval: interval to set 
             :type interval: integer

        """
        for i in periodical.jobs:
            if i.pid == pid:
                i.interval = interval
                i.next = time.time() + interval

    def looponce(self):
        """ do one loop over the jobs. """
        for job in self.jobs:
            if job.next <= time.time():
                self.runjob(job)

    def checkloop(self):
        """ main loop of the periodical scheduler."""
        logging.info("periodical - starting checkloop")
        self.run = True
        while self.run:
            for job in self.jobs:
                if job.next <= time.time():
                    self.runjob(job)

            time.sleep(self.SLEEPTIME)
        logging.info("periodical - stopping checkloop")

    def runjob(self, job):
        """ run a periodical job. """
        if not job.check():
            self.killjob(job.id())
        else:
            self.running.append(job)

    def kill(self):
        ''' kill all jobs invoked by a modul. '''
        group = calledfrom(sys._getframe())
        self.killgroup(group)

    def killgroup(self, group):
        """ kill all jobs with the same group. """

        def shoot():
            """ knock down all jobs belonging to group. """
            deljobs = [job for job in self.jobs if job.member(group)]
            for job in deljobs:
                self.jobs.remove(job)
                try:
                    self.running.remove(job)
                except ValueError:
                    pass

            logging.debug('periodical - killed %d jobs for %s' % (len(deljobs), group))
            del deljobs

        shoot() # *pow* you're dead ;)

    def killjob(self, jobId):
        """ kill one job by its id. """

        def shoot():
            deljobs = [x for x in self.jobs if x.id() == jobId]
            numjobs = len(deljobs)
            for job in deljobs:
                self.jobs.remove(job)
                try:
                    self.running.remove(job)
                except ValueError:
                    pass
            del deljobs
            return numjobs

        return shoot() # *pow* you're dead ;)


## functions

def interval(sleeptime, repeat=0):
    """
        interval decorator.

        :param sleeptime: time to sleep
        :type sleeptime: integer
        :param repeat: number of times to repeat the job
        :type repeat: integet

    """
    group = calledfrom(sys._getframe())

    def decorator(function):
        decorator.func_dict = function.func_dict

        def wrapper(*args, **kw):
            job = JobInterval(sleeptime, repeat, function, *args, **kw)
            job.group = group
            job.description = whichmodule()
            periodical.jobs.append(job)

        return wrapper

    return decorator

def at(start, interval=1, repeat=1):
    """
        at decorator.

        :param start: start time of the periodical job
        :type start: integer, float or string
        :param interval: time between jobs
        :type sleeptime: integer
        :param repeat: number of times to repeat the job
        :type repeat: integet

    """
    group = calledfrom(sys._getframe())

    def decorator(function):
        decorator.func_dict = function.func_dict

        def wrapper(*args, **kw):
            job = JobAt(start, interval, repeat, function, *args, **kw)
            job.group = group
            job.description = whichmodule()
            periodical.jobs.append(job)

        wrapper.func_dict = function.func_dict
        return wrapper

    return decorator

def persecond(function):
    """
        per second decorator.

        :param function: function to execute every second
        :type function: function

    """
    minutely.func_dict = function.func_dict
    group = calledfrom(sys._getframe())

    def wrapper(*args, **kw):
        job = JobInterval(1, 0, function, *args, **kw)
        job.group = group
        job.description = whichmodule()
        periodical.jobs.append(job)

    return wrapper

def minutely(function):
    """
        minute decorator.

        :param function: function to execute every minute
        :type function: function

    """
    minutely.func_dict = function.func_dict
    group = calledfrom(sys._getframe())

    def wrapper(*args, **kw):
        job = JobInterval(60, 0, function, *args, **kw)
        job.group = group
        job.description = whichmodule()
        periodical.jobs.append(job)

    return wrapper

def hourly(function):
    """
        hour decorator.

        :param function: function to execute every hour
        :type function: function

    """
    hourly.func_dict = function.func_dict
    group = calledfrom(sys._getframe())

    def wrapper(*args, **kw):
        job = JobInterval(3600, 0, function, *args, **kw)
        job.group = group
        job.description = whichmodule()
        periodical.jobs.append(job)

    return wrapper

def daily(function):
    """
        day decorator.

        :param function: function to execute every hour
        :type function: function

    """
    daily.func_dict = function.func_dict
    group = calledfrom(sys._getframe())

    def wrapper(*args, **kw):
        job = JobInterval(86400, 0, function, *args, **kw)
        job.group =  group
        job.description = whichmodule()
        periodical.jobs.append(job)

    return wrapper

## define

# the periodical scheduler
periodical = Periodical()
