# gozerlib/threads.py
#
#

""" own threading wrapper. """

## gozerlib imports

from utils.exception import handle_exception

## basic imports

import threading
import re
import time
import thread
import logging
import uuid

## defines

# RE to determine thread name

methodre = re.compile('method\s+(\S+)', re.I)
funcre = re.compile('function\s+(\S+)', re.I)

## defer to task (GAE)

def task(func):
    try:
        from google.appengine.ext.deferred import defer
        task.defer = lambda *args, **kwargs: defer(func, *args, **kwargs)
    except ImportError: pass
    return task

## BotEvent class

try: 
    from google.appengine.api.labs.taskqueue import Task
    from simplejson import dumps

    class BotEvent(Task):
        pass

    def start_botevent(bot, event):
        """ start a new botevent task. """
        try:
            event.botevent = True
            name = event.usercmnd + "-" + str(uuid.uuid4())
            payload = dumps({ 'bot': bot.tojson(),
                        'event': event.tojson()
                      })
            be = BotEvent(name=name, payload=payload, url="/tasks/botevent")
            be.add()
        except Exception, ex:
            handle_exception()
except ImportError: logging.info("No BotEvent defined.")
except Exception, ex: handle_exception()

## Botcommand class

class Botcommand(threading.Thread):

    """ thread for running bot commands. """

    def __init__(self, group, target, name, args, kwargs):
        threading.Thread.__init__(self, None, target, name, args, kwargs)
        self.name = name
        self.ievent = args[1]
        self.setDaemon(True)

    def run(self):
        """ run the bot command. """
        
        try:
            result = threading.Thread.run(self)
            if self.ievent.closequeue:
                logging.debug('threads- closing queue for %s' % self.ievent.userhost)
                if self.ievent.queues:
                    for i in self.ievent.queues: i.put_nowait(None)
            if self.ievent.outqueue: self.ievent.outqueue.put_nowait(None)
            if self.ievent.inqueue: self.ievent.inqueue.put_nowait(None)
        except Exception, ex:
            handle_exception(self.ievent)
            time.sleep(1)

## Thr class

class Thr(threading.Thread):

    """ thread wrapper. """

    def __init__(self, group, target, name, args, kwargs):
        threading.Thread.__init__(self, None, target, name, args, kwargs)
        self.setDaemon(True)
        self.name = name

    def run(self):
        """ run the thread. """
        try:
            logging.debug('threads - running thread %s' % self.name) 
            threading.Thread.run(self)
        except Exception, ex:
            handle_exception()
            time.sleep(1)

## getname function

def getname(func):
    """ get name of function/method. """
    name = ""
    method = re.search(methodre, str(func))
    if method: name = method.group(1)
    else: 
        function = re.search(funcre, str(func))
        if function: name = function.group(1)
        else: name = str(func)
    return name

## start_new_thread function

def start_new_thread(func, arglist, kwargs={}):
    """ start a new thread .. set name to function/method name."""
    if not kwargs: kwargs = {}
    if not 'name' in kwargs:
        name = getname(func)
        if not name: name = str(func)
    else: name = kwargs['name']
    try:
        thread = Thr(None, target=func, name=name, args=arglist, kwargs=kwargs)
        thread.start()
        return thread
    except thread.error, ex:
        if "can't start" in str(ex):
            logging.error("threads - thread space is exhausted - can't start thread %s" % name)
            handle_exception()
            time.sleep(3)
    except:
        handle_exception()
        time.sleep(3)

## start_bot_cpmmand function

def start_bot_command(func, arglist, kwargs={}):
    """ start a new thread .. set name to function/method name. """
    if not kwargs: kwargs = {}
    try:
        name = getname(func)
        if not name: name = 'noname'
        thread = Botcommand(group=None, target=func, name=name, args=arglist, kwargs=kwargs)
        thread.start()
        return thread
    except:
        handle_exception()
        time.sleep(1)


def threaded(func):
    """ threading decorator. """
    def threadedfunc(*args, **kwargs):
        start_new_thread(func, args, kwargs)
    return threadedfunc
