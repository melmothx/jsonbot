# gozerlib/botbase.py
#
#

""" base class for all bots. """

## gozerlib imports

from utils.exception import handle_exception
from runner import defaultrunner
from eventhandler import mainhandler
from utils.lazydict import LazyDict
from plugins import plugs as coreplugs
from callbacks import callbacks, first_callbacks, last_callbacks, remote_callbacks
from eventbase import EventBase
from errors import NoSuchCommand, PlugsNotConnected, NoOwnerSet, NameNotSet, NoEventProvided
from datadir import datadir
from commands import Commands
from config import Config
from utils.pdod import Pdod
from channelbase import ChannelBase
from less import Less
from boot import boot
from utils.locking import lockdec
from exit import globalshutdown
from utils.generic import splittxt, toenc, fromenc, waitforqueue, strippedtxt
from utils.trace import whichmodule
from fleet import fleet
from utils.name import stripname
from tick import tickloop
from threads import start_new_thread, threaded
from gatekeeper import GateKeeper

## basic imports

import time
import logging
import copy
import sys
import getpass
import os
import thread
import types
import threading
import Queue
import re

## defines

cpy = copy.deepcopy

## locks

reconnectlock = threading.RLock()
reconnectlocked = lockdec(reconnectlock)

lock = thread.allocate_lock()
locked = lockdec(lock)

## classes

class BotBase(LazyDict):

    """ base class for all bots. """

    def __init__(self, cfg=None, usersin=None, plugs=None, botname=None, nick=None, *args, **kwargs):
        if not botname and cfg: botname = cfg.botname
        if botname: self.botname = botname
        else: self.botname = u"default-%s" % str(type(self)).split('.')[-1][:-2]
        logging.debug("botbase - name is %s" % self.botname)
        self.fleetdir = u'fleet' + os.sep + stripname(self.botname)
        if cfg: self.update(cfg)
        self.cfg = cfg or Config(self.fleetdir + os.sep + u'config')
        LazyDict.__init__(self)
        self.inqueue = Queue.Queue()
        self.outqueue = Queue.Queue()
        self.reconnectcount = 0
        self.stopped = False
        self.plugs = plugs or coreplugs
        self.gatekeeper = GateKeeper(self.botname)
        self.gatekeeper.allow(self.user or self.jid or self.server or self.botname)
        self.closed = False
        try:
            import waveapi
            self.isgae = True
            logging.debug("botbase - bot is a GAE bot (%s)" % self.botname)
        except ImportError:
            self.isgae = False
            logging.debug("botbase - bot is a shell bot (%s)" % self.botname)
        self.starttime = time.time()
        self.type = "base"
        self.status = "init"
        self.networkname = self.cfg.networkname or self.botname or ""
        if not self.uuid:
            if self.cfg and self.cfg.uuid: self.uuid = self.cfg.uuid
            else:
                self.uuid = self.cfg.uuid = uuid.uuid4()
                self.cfg.save()
        if self.cfg and not self.cfg.followlist: self.cfg.followlist = [] ; self.cfg.save()
        self.datadir = datadir + os.sep + self.fleetdir
        self.name = self.botname
        self.owner = self.cfg.owner
        if not self.owner:
            logging.debug(u"owner is not set in %s - using mainconfig" % self.cfg.cfile)
            from config import cfg as mainconfig
            self.owner = mainconfig.owner
        self.setusers(usersin)
        logging.info(u"botbase - owner is %s" % self.owner)
        self.users.make_owner(self.owner)
        self.outcache = Less(3)
        self.userhosts = {}
        self.connectok = threading.Event()
        if not self.nick: self.nick = nick or self.cfg.nick or u'jsonbot'
        try:
            if not os.isdir(self.datadir): os.mkdir(self.datadir)
        except: pass
        self.setstate()
        self.stopreadloop = False
        self.stopoutloop = False
        self.outputlock = thread.allocate_lock()
        self.outqueues = [Queue.Queue() for i in range(10)]
        self.tickqueue = Queue.Queue()
        self.encoding = self.cfg.encoding or "utf-8"
        if not fleet.byname(self.name): fleet.bots.append(self)
        if not self.isgae:
            defaultrunner.start()
            tickloop.start(self)

    def put(self, event):
        self.inqueue.put_nowait(event)

    def broadcast(self, txt):
        for chan in self.state['joinedchannels']:
            self.say(chan, txt)

    def _eventloop(self):
        """ fetch events from the inqueue and handle them. """
        logging.debug("%s - eventloop started" % self.name)
        while not self.stopped:
            event = self.inqueue.get()
            if not event: break
            self.doevent(event)
        logging.debug("%s - eventloop stopped" % self.name)

    def _getqueue(self):
        """ get one of the outqueues. """
        go = self.tickqueue.get()
        for index in range(len(self.outqueues)):
            if not self.outqueues[index].empty(): return self.outqueues[index]

    def _outloop(self):
        """ output loop. """
        logging.debug('%s - starting output loop' % self.name)
        self.stopoutloop = 0
        while not self.stopped and not self.stopoutloop:
            queue = self._getqueue()
            if queue:
                try:
                    res = queue.get() 
                except Queue.Empty: continue
                if not res: continue
                if not self.stopped and not self.stopoutloop:
                    logging.debug("%s - OUT - %s - %s" % (self.name, self.type, str(res))) 
                    self.out(*res)
            time.sleep(0.1)
        logging.debug('%s - stopping output loop' % self.name)

    def putonqueue(self, nr, *args):
        """ put output onto one of the output queues. """
        self.outqueues[10-nr].put_nowait(args)
        self.tickqueue.put_nowait('go')

    def outputsizes(self):
        """ return sizes of output queues. """
        result = []  
        for q in self.outqueues:
            result.append(q.qsize())
        return result

    def setstate(self, state=None):
        """ set state on the bot. """
        self.state = state or Pdod(self.datadir + os.sep + 'state')
        if self.state and not 'joinedchannels' in self.state.data: self.state.data.joinedchannels = []

    def setusers(self, users=None):
        """ set users on the bot. """
        if users:
            self.users = users
            return
        import gozerlib.users as u
        if not u.users: u.users_boot()
        self.users = u.users

    def loadplugs(self, packagelist=[]):
        """ load plugins from packagelist. """
        self.plugs.loadall(packagelist)
        return self.plugs

    def joinchannels(self):
        """ join channels. """
        from config import cfg as mainconfig
        time.sleep(mainconfig.waitforjoin or 5)
        for i in self.state['joinedchannels']:
            try:
                logging.debug("%s - joining %s" % (self.name, i))
                channel = ChannelBase(i)
                if channel: key = channel.getpass()
                else: key=None
                start_new_thread(self.join, (i, key))
                time.sleep(1)
            except Exception, ex:
                logging.warn('%s - failed to join %s: %s' % (self.name, i, str(ex)))
                handle_exception()

    def start(self, connect=True):
        """ start the mainloop of the bot. """
        if not self.isgae: 
            if connect: self.connect()
            start_new_thread(self._outloop, ())
            start_new_thread(self._eventloop, ())
            start_new_thread(self._readloop, ())
            if connect:
                self.connectok.wait(30)
                if self.connectok.isSet():
                    start_new_thread(self.joinchannels, ())
        self.status == "running"
        self.dostart(self.botname, self.type)

    def doremote(self, event):
        """ dispatch an event. """
        if not event: raise NoEventProvided()
        self.status = "callback"
        starttime = time.time()
        msg = "%s - %s - %s - %s" % (self.name.upper(), event.cbtype, event.auth, event.how)
        logging.warn(msg)
        logging.debug("botbase - remote - %s" % event.dump())
        if self.closed:
            if self.gatekeeper.isblocked(event.origin): return
        if event.status == "done":
            logging.debug("%s - event is done .. ignoring" % self.name)
            return
        self.reloadcheck(event)
        e0 = cpy(event)
        e0.speed = 1
        remote_callbacks.check(self, e0)
        return

    #@locked
    def doevent(self, event):
        """ dispatch an event. """
        if not event: raise NoEventProvided()
        if event.isremote(): self.doremote(event) ; return
        self.status = "callback"
        starttime = time.time()
        msg = "%s - %s - %s - %s" % (self.name.upper(), event.cbtype, event.auth, event.how)
        if event.cbtype in ['NOTICE']: logging.warn("%s - %s - %s" % (self.name, event.nick, event.txt))
        else:
            try: int(event.cbtype) ; logging.debug(msg)
            except ValueError:
                if event.cbtype == 'PING': logging.debug(msg)
                else: logging.warn(msg)
        logging.debug("%s - %s" % (self.name, event.tojson()))
        if self.closed:
            if self.gatekeeper.isblocked(event.origin): return
        if event.status == "done":
            logging.debug("%s - event is done .. ignoring" % self.name)
            return
        self.reloadcheck(event)
        if event.msg or event.isdcc: event.speed = 2
        e1 = cpy(event)
        #e2 = cpy(event)
        #e3 = cpy(event)
        callbacks.check(self, e1)
        #if not event.forwarded:
        #    e2 = cpy(event)
        #    callbacks.check(self, e2)
        #    e3 = cpy(event)
        #    last_callbacks.check(self, e3)
        event.callbackdone = True
        return event

    def ownercheck(self, userhost):
        """ check if provided userhost belongs to an owner. """
        if self.cfg and self.cfg.owner:
            if userhost in self.cfg.owner: return True
        return False

    def exit(self):
        """ exit the bot. """ 
        logging.warn("%s - exit" % self.name)
        if not self.stopped: self.quit()
        self.stopped = True   
        self.stopreadloop = True  
        self.connected = False
        self.put(None)
        self.tickqueue.put_nowait('go')
        self.outqueue.put_nowait(None)
        self.shutdown()
        self.save()

    def _raw(self, txt, *args, **kwargs):
        """ override this. """ 
        logging.warn(u"%s - out - %s" % (self.name, txt))
        print txt

    def makeoutput(self, printto, txt, result=[], nr=375, extend=0, dot=", ", *args, **kwargs):
        if not txt: return ""
        txt = self.makeresponse(txt, result, dot)
        res1, nritems = self.less(printto, txt, nr+extend)
        return res1

    def out(self, printto, txt, how="msg", event=None, origin=None, *args, **kwargs):
        self.outnocb(printto, txt, how, event, *args, **kwargs)
        self.outmonitor(self.me, printto, txt)

    write = out

    def outnocb(self, printto, txt, how="msg", event=None, html=False, *args, **kwargs):
        self._raw(txt)

    writenocb = outnocb

    def say(self, channel, txt, result=[], how="msg", event=None, nr=375, extend=0, dot=", ", *args, **kwargs):
        txt = self.makeoutput(channel, txt, result, nr, extend, dot, *args, **kwargs)
        if txt: self.out(channel, txt, how, event, *args, **kwargs)
        
    def saynocb(self, channel, txt, result=[], how="msg", event=None, nr=375, extend=0, dot=", ", *args, **kwargs):
        txt = self.makeoutput(channel, txt, result, nr, extend, dot, *args, **kwargs)
        if txt: self.outnocb(channel, txt, event=event, *args, **kwargs)

    def less(self, printto, what, nr=365):
        """ split up in parts of <nr> chars overflowing on word boundaries. """
        if type(what) == types.ListType: txtlist = what
        else:
            what = what.strip()
            txtlist = splittxt(what, nr)
        size = 0
        if not txtlist:   
            logging.debug("can't split txt from %s" % what)
            return ["", ""]
        res = txtlist[0]
        length = len(txtlist)
        if length > 1:
            logging.debug("addding %s lines to %s outputcache" % (len(txtlist), printto))
            self.outcache.set(printto, txtlist[1:])
            res += "<b> - %s more</b>" % (length - 1) 
        return [res, length]

    def join(self, channel, password, *args, **kwargs):
        """ join a channel. """
        pass

    def part(self, channel, *args, **kwargs):
        """ leave a channel. """
        pass

    def action(self, channel, txt, *args, **kwargs):
        """ send action to channel. """
        pass

    def reconnect(self):
        """ reconnect to the server. """
        try:
            try: self.exit()
            except Exception, ex: handle_exception()
            self.reconnectcount += 1
            logging.warn('%s - reconnecting .. sleeping %s seconds' % (self.name, self.reconnectcount*15))
            time.sleep(self.reconnectcount * 15)   
            self.doreconnect()
        except Exception, ex: 
            handle_exception()

    def doreconnect(self):
        self.start(connect=True)

    def invite(self, *args, **kwargs):
        """ invite another user/bot. """
        pass

    def donick(self, nick, *args, **kwargs):
        """ do a nick change. """
        pass

    def shutdown(self, *args, **kwargs):
        """ shutdown the bot. """
        pass

    def quit(self, reason="", *args, **kwargs):
        """ close connection with the server. """
        pass

    def connect(self, reconnect=True, *args, **kwargs):
        """ connect to the server. """
        pass

    def names(self, channel, *args, **kwargs):
        """ request all names of a channel. """
        pass

    def save(self, *args, **kwargs):
        """ save bot state if available. """
        if self.state: self.state.save()

    def makeresponse(self, txt, result=[], dot=", ", *args, **kwargs):
        """ create a response from a string and result list. """
        res = []
        if result:
            for i in result:
                if not i: continue
                if type(i) == types.ListType or type(i) == types.TupleType:
                    try:
                        res.append(dot.join(i))
                    except TypeError: res.extend(i)
                else: res.append(i)
        if txt: return unicode(txt) + dot.join(res)   
        elif res: return dot.join(res)
        return ""
    
    def reloadcheck(self, event):
        """ check if plugin need to be reloaded for callback, """
        plugloaded = []
        target = event.cbtype or event.cmnd
        #logging.debug("botbase - checking for reload of %s (%s)" % (target, event.userhost))
        try:
            from boot import getcallbacktable   
            plugins = getcallbacktable()[target]
        except KeyError:
            logging.debug("botbase - can't find plugin to reload for %s" % event.cmnd)
            return
        from plugins import plugs
        for name in plugins: 
            if name in plugs:
                logging.debug("botbase - %s already loaded" % name)
                continue
            else:
                logging.warn("botbase - on demand reloading of %s" % name)
                try:
                    plugloaded.append(plugs.reload(name, showerror=True))
                except Exception, ex: handle_exception(event)
        return plugloaded

    def send(self, *args, **kwargs):
        pass

    def sendnocb(self, *args, **kwargs):
        pass

    def normalize(self, what):
        """ convert markup to IRC bold. """
        txt = strippedtxt(what)
        txt = re.sub("\s+", " ", what)
        txt = txt.replace("<b>", "\002")
        txt = txt.replace("</b>", "\002")
        txt = txt.replace("<i>", "")
        txt = txt.replace("</i>", "")
        txt = txt.replace("&lt;b&gt;", "\002")
        txt = txt.replace("&lt;/b&gt;", "\002")
        txt = txt.replace("&lt;i&gt;", "")
        txt = txt.replace("&lt;/i&gt;", "")
        txt = txt.replace("&lt;h2&gt;", "\002")
        txt = txt.replace("&lt;/h2&gt;", "\002")
        txt = txt.replace("&lt;h3&gt;", "\002")
        txt = txt.replace("&lt;/h3&gt;", "\002")
        txt = txt.replace("&lt;li&gt;", "\002")
        txt = txt.replace("&lt;/li&gt;", "\002")
        return txt

    def dostart(self, botname, bottype, *args, **kwargs):
        """ create an START event and send it to callbacks. """
        e = EventBase()
        e.bot = self
        e.botname = botname
        e.bottype = bottype
        e.origin = botname
        e.ruserhost = self.botname +'@' + self.uuid
        e.userhost = e.ruserhost
        e.channel = botname
        e.origtxt = str(time.time())
        e.txt = e.origtxt
        e.cbtype = 'START'
        e.botoutput = False
        e.ttl = 1
        e.nick = self.nick or self.botname
        self.doevent(e)
        logging.warn("%s - START event send to callbacks" % botname)

    def outmonitor(self, origin, channel, txt, event=None):
        """ create an OUTPUT event with provided txt and send it to callbacks. """
        e = EventBase()
        if event: e.copyin(event)
        if e.status == "done":
            logging.debug("%s - outmonitor - event is done .. ignoring" % self.name)
            return
        e.bot = self
        e.origin = origin
        e.ruserhost = self.botname +'@' + self.uuid
        e.userhost = e.ruserhost
        e.channel = channel
        e.origtxt = txt
        e.txt = txt
        e.cbtype = 'OUTPUT'
        e.botoutput = True
        e.ttl = 1
        e.nick = self.nick or self.botname
        e.prepare()
        first_callbacks.check(self, e)

    def docmnd(self, origin, channel, txt, event=None, wait=0):
        """ do a command. """
        e = EventBase()
        if event: e.copyin(event)
        e.bot = self
        e.origin = origin
        e.ruserhost = origin
        e.auth = origin
        e.userhost = origin
        e.channel = channel
        e.txt = txt
        e.nick = e.userhost.split('@')[0]
        e.usercmnd = e.txt.split()[0]
        e.closequeue = True
        if wait: e.direct = True
        e.bind(self)
        try:
            event = self.plugs.dispatch(self, e, wait=wait)
            return event
        except NoSuchCommand: e.reply("no such command: %s" % e.usercmnd)
