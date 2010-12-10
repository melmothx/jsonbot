# gozerlib/gae/tasks.py
#
#

""" appengine tasks related classes and functions. """

## gozerlib imports

from gozerlib.utils.exception import handle_exception

## google imports

from google.appengine.api.labs.taskqueue import Task, Queue

## simplejson imports

from simplejson import dumps

## basic imports

import uuid

## Event Classes

class BotEvent(Task):
    pass

## defines

queues = []
for i in range(10):
    queues.append(Queue("queue" + str(i)))

## start_botevent function

def start_botevent(bot, event, speed=5):
    """ start a new botevent task. """
    try:
        event.botevent = True
        name = event.usercmnd[1:] + "-" + str(uuid.uuid4())
        payload = dumps({ 'bot': bot.tojson(),
                          'event': event.tojson()
                        })
        be = BotEvent(name=name, payload=payload, url="/tasks/botevent")
        try: queues[int(speed)].add(be)
        except TypeError: queues[speed].add(be)
    except Exception, ex: 
        handle_exception()
