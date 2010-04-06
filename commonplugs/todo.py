# commonplugs/todo.py
#
#

""" manage todo lists per users .. a time/data string can be provided to set 
    time on a todo item.
"""

## gozerlib imports

from gozerlib.utils.generic import getwho
from gozerlib.utils.timeutils import strtotime, striptime, today
from gozerlib.utils.locking import lockdec
from gozerlib.utils.exception import handle_exception
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.users import users
from gozerlib.datadir import datadir
from gozerlib.persist import PlugPersist
from gozerlib.persiststate import UserState
from gozerlib.config import cfg as config
from gozerlib.utils.lazydict import LazyDict

## basic imports

import time
import thread
import os
from datetime import datetime, timedelta
from time import localtime

## defines

todolock = thread.allocate_lock()
locked = lockdec(todolock)

class Todo(LazyDict):
    pass

class TodoList(UserState):

    def __init__(self, name, *args, **kwargs):
        UserState.__init__(self, name, "todo", *args, **kwargs)
        if self.data.list:
            self.data.list = [LazyDict(x) for x in self.data.list]
        else:
            self.data.list = []

    def add(self, txt, ttime=0, duration=0, warnsec=0, priority=0):
        """ add a todo """
        todo = Todo()
        todo.time = ttime
        todo.duration = duration
        todo.warnsec = warnsec
        todo.priority = priority
        todo.txt = txt.strip()
        self.data.list.append(todo)
        self.save()
        return len(self.data.list)

    def delete(self, indexnr):
        del self.data.list[indexnr]
        self.save()
        return self

    def clear(self):
        self.data.list = []
        self.save()
        return self

    def toolate(self):
        res = []
        now = time.time()
        for todo in self.data.list:
            if todo.time < now:
                res.append(todo)
        return res

    def withintime(self, before, after):
        res = []
        for todo in self.data.list:
            if todo.time > before and todo.time < after:
                res.append(todo)
        return res

    def timetodo(self):
        min = 0        
        res = []
        for todo in self.data.list:
            if todo.time > min:
                res.append(todo)
        return res

def handle_todo(bot, ievent):
    """ todo [<item>] .. show todo's or set todo item .. a time/date can be \
given"""
    if len(ievent.args) > 0:
        handle_todo2(bot, ievent)
        return
    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    try:
        todoos = TodoList(name).data.list
    except KeyError:
        ievent.reply('i dont have todo info for %s' % user.name)
        return
    saytodo(bot, ievent, todoos)

def handle_todo2(bot, ievent):
    """ set todo item """
    if not ievent.rest:
        ievent.missing("<what>")
        return
    else:
        what = ievent.rest
    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    ttime = strtotime(what)
    nr = 0
    todo = TodoList(name)
    if not ttime == None:
        ievent.reply('time detected ' + time.ctime(ttime))
        nr = todo.add(what, ttime)
    else:
        nr = todo.add(what)
    ievent.reply('todo item %s added' % nr)

cmnds.add('todo', handle_todo, ['USER', 'GUEST'])
examples.add('todo', 'todo [<item>] .. show todo items or add a todo item', \
'1) todo 2) todo program the bot 3) todo 22:00 sleep')

def handle_tododone(bot, ievent):
    """ todo-done <listofnrs> .. remove todo items """
    if len(ievent.args) == 0:
        ievent.missing('<list of nrs>')
        return
    try:
        nrs = []
        for i in ievent.args:
            nrs.append(int(i))
        nrs.sort()
    except ValueError:
        ievent.reply('%s is not an integer' % i)
        return
    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    nrdone = 0
    failed = []
    todo = TodoList(name)
    for i in nrs[::-1]:
        try:
            del todo.data.list[i]
            nrdone += 1
        except IndexError:
            continue
        except Exception, ex:
            failed.append(str(i))
            handle_exception()
    if failed:
        ievent.reply('failed to delete %s' % ' .. '.join(failed))
    if nrdone == 1:
        todo.save()
        ievent.reply('%s item deleted' % nrdone)
    elif nrdone == 0:
        ievent.reply('no items deleted')
    else:
        todo.save()
        ievent.reply('%s items deleted' % nrdone)

cmnds.add('todo-done', handle_tododone, ['USER', 'GUEST'])
examples.add('todo-done', 'todo-done <listofnrs> .. remove items from \
todo list', '1) todo-done 1 2) todo-done 3 5 8')

def handle_settodo(bot, ievent):
    """ todo-set <name> <txt> .. add a todo to another user's todo list"""
    try:
        who = ievent.args[0]
        what = ' '.join(ievent.args[1:])
    except IndexError:
        ievent.missing('<nick> <what>')
        return
    if not what:
        ievent.missing('<nick> <what>')
        return
    userhost = getwho(bot, who)
    if not userhost:
        ievent.reply("can't find userhost for %s" % who)
        return
    whouser = bot.users.getname(userhost)
    if not whouser:
        ievent.reply("can't find user for %s" % userhost)
        return
    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    if not bot.users.permitted(userhost, name, 'todo'):
        ievent.reply("%s doesn't permit todo sharing for %s " % \
(who, name))
        return
    what = "%s: %s" % (ievent.nick, what)
    ttime = strtotime(what)
    nr = 0
    todo = TodoList(name)
    if not ttime  == None:
        ievent.reply('time detected ' + time.ctime(ttime))
        what = striptime(what)
        nr = todo.add(what, ttime)
    else:
        nr = todo.add(what)
    ievent.reply('todo item %s added' % nr)

cmnds.add('todo-set', handle_settodo, 'USER')
examples.add('todo-set', 'todo-set <nick> <txt> .. set todo item of \
<nick>', 'todo-set dunker bot proggen')

def handle_gettodo(bot, ievent):
    """ todo-get <nick> .. get todo of another user """
    try:
        who = ievent.args[0]
    except IndexError:
        ievent.missing('<nick>')
        return
    userhost = getwho(bot, who)
    if not userhost:
        ievent.reply("can't find userhost for %s" % who)
        return
    whouser = bot.users.getname(userhost)
    if not whouser:
        ievent.reply("can't find user for %s" % userhost)
        return
    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    if not bot.users.permitted(userhost, name, 'todo'):
        ievent.reply("%s doesn't permit todo sharing for %s " % (who, name))
        return
    todo = TodoList(name)
    todoos = todo.get(whouser)
    saytodo(bot, ievent, todoos)

cmnds.add('todo-get', handle_gettodo, ['USER', 'GUEST'])
examples.add('todo-get', 'todo-get <nick> .. get the todo list of \
<nick>', 'todo-get dunker')

def handle_todotime(bot, ievent):
    """ todo-time .. show time related todoos """
    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    todo = TodoList(name)
    todoos = todo.timetodo()
    saytodo(bot, ievent, todoos)

cmnds.add('todo-time', handle_todotime, ['USER', 'GUEST'])
examples.add('todo-time', 'todo-time .. show todo items with time fields', \
'todo-time')

def handle_todoweek(bot, ievent):
    """ todo-week .. show time related todo items for this week """
    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    todo = TodoList(name)
    todoos = todo.withintime(today(), today()+7*24*60*60)
    saytodo(bot, ievent, todoos)

cmnds.add('todo-week', handle_todoweek, ['USER', 'GUEST'])
examples.add('todo-week', 'todo-week .. todo items for this week', 'todo-week')

def handle_today(bot, ievent):
    """ todo-today .. show time related todo items for today """
    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    todo = TodoList(name)
    now = time.time()
    todoos = todo.withintime(now, now+3600*24)
    saytodo(bot, ievent, todoos)

cmnds.add('todo-today', handle_today, ['USER', 'GUEST'])
examples.add('todo-today', 'todo-today .. todo items for today', 'todo-today')

def handle_tomorrow(bot, ievent):
    """ todo-tomorrow .. show time related todo items for tomorrow """
    username = bot.users.getname(ievent.userhost)
    if not username:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    todo = TodoList(username)
    if ievent.rest:
        what = ievent.rest
        ttime = strtotime(what)
        if ttime != None:
            if ttime < today() or ttime > today() + 24*60*60:
                ievent.reply("%s is not tomorrow" % time.ctime(ttime + 24*60*60))
                return
            ttime += 24*60*60
            ievent.reply('time detected ' + time.ctime(ttime))
            what = striptime(what)
        else:
            ttime = today() + 42*60*60
        todo.add(what, ttime)   
        ievent.reply('todo added')    
        return
    todoos = todo.withintime(today()+24*60*60, today()+2*24*60*60)
    saytodo(bot, ievent, todoos)

cmnds.add('todo-tomorrow', handle_tomorrow, ['USER', 'GUEST'])
examples.add('todo-tomorrow', 'todo-tomorrow .. todo items for tomorrow', \
'todo-tomorrow')

def handle_setpriority(bot, ievent):
    """ todo-setprio [<channel|name>] <itemnr> <prio> .. show priority \
        on todo item """
    try:
        (who, itemnr, prio) = ievent.args
    except ValueError:
        try:
            (itemnr, prio) = ievent.args
            who = bot.users.getname(ievent.userhost)
        except ValueError:
            ievent.missing('[<channe|namel>] <itemnr> <priority>')
            return
    if not who:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    try:
        itemnr = int(itemnr)
        prio = int(prio)
    except ValueError:
        ievent.missing('[<channel|name>] <itemnr> <priority>')
        return
    todo = TodoList(who)
    try:
        todo.data.list[itemnr].priority = prio
        todo.save()
        ievent.reply('priority set')
    except IndexError:
        ievent.reply("no %s item in todolist" % str(itemnr))

cmnds.add('todo-setprio', handle_setpriority, ['USER', 'GUEST'])
examples.add('todo-setprio', 'todo-setprio [<channel|name>] <itemnr> <prio> \
.. set todo priority', '1) todo-setprio #dunkbots 2 5 2) todo-setprio owner \
3 10 3) todo-setprio 2 10')

def handle_todosettime(bot, ievent):
    """ todo-settime [<channel|name>] <itemnr> <timestring> .. set time \
        on todo item """
    ttime = strtotime(ievent.rest)
    if ttime == None:
        ievent.reply("can't detect time")
        return   
    txt = striptime(ievent.rest)
    try:
        (who, itemnr) = txt.split()
    except ValueError:
        try:
            (itemnr, ) = txt.split()
            who = bot.users.getname(ievent.userhost)
        except ValueError:
            ievent.missing('[<channel|name>] <itemnr> <timestring>')
            return
    if not who:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    try:
        itemnr = int(itemnr)
    except ValueError:
        ievent.missing('[<channel|name>] <itemnr> <timestring>')
        return
    todo = TodoList(who)
    try:
        todo.data.list[itemnr].time = ttime
        todo.save()
        ievent.reply('time of todo %s set to %s' % (itemnr, time.ctime(ttime)))
    except IndexError:
        ievent.reply("%s item in todolist" % str(itemnr))

cmnds.add('todo-settime', handle_todosettime, ['USER', 'GUEST'])
examples.add('todo-settime', 'todo-settime [<channel|name>] <itemnr> \
<timestring> .. set todo time', '1) todo-settime #dunkbots 2 13:00 2) \
todo-settime owner 3 2-2-2010 3) todo-settime 2 22:00')

def handle_getpriority(bot, ievent):
    """ todo-getprio <[channel|name]> <itemnr> .. get priority of todo \
        item """
    try:
        (who, itemnr) = ievent.args
    except ValueError:
        try:
            itemnr = ievent.args[0]
            who = bot.users.getname(ievent.userhost)
        except IndexError:
            ievent.missing('[<channel|name>] <itemnr>')
            return
    if not who:
        ievent.reply("can't find username for %s" % ievent.userhost)
        return
    try:
        itemnr = int(itemnr)
    except ValueError:
        ievent.missing('[<channel|name>] <itemnr>')
        return
    
    todo = TodoList(who)
    try:
        prio = todo.data.list[itemnr].priority
        ievent.reply('priority is %s' % prio)
    except IndexError:
        ievent.reply("%s item in todolist" % str(itemnr))


cmnds.add('todo-getprio', handle_getpriority, ['USER', 'GUEST'])
examples.add('todo-getprio', 'todo-getprio [<channel|name>] <itemnr> .. get \
todo priority', '1) todo-getprio #dunkbots 5 2) todo-getprio 3')

def saytodo(bot, ievent, todoos):
    """ output todo items of <name> """
    if not todoos:
        ievent.reply('nothing todo ;]')
        return
    result = []
    now = time.time()
    counter = 0
    for i in todoos:
        res = ""
        res += "%s) " % counter
        counter += 1
        if i.priority:
            res += "[%s] " % i.priority
        if i.time and not i.time == 0:
            if i.time < now:
                res += 'TOO LATE: '
            res += "%s %s " % (time.ctime(float(i.time)), i.txt)
        else:
            res += "%s " % i.txt
        result.append(res.strip())
    if result:
        ievent.reply("todo: ", result, dot=" ")
