# jsb/botbase.py
#
#

""" base class for all bots. """

## jsb imports

from jsb.utils.exception import handle_exception
from runner import defaultrunner
from eventhandler import mainhandler
from jsb.utils.lazydict import LazyDict
from plugins import plugs as coreplugs
from callbacks import callbacks, first_callbacks, last_callbacks, remote_callbacks
from eventbase import EventBase
from errors import NoSuchCommand, PlugsNotConnected, NoOwnerSet, NameNotSet, NoEventProvided
from commands import Commands, cmnds
from config import Config
from jsb.utils.pdod import Pdod
from channelbase import ChannelBase
from less import Less, outcache
from boot import boot, getcmndperms, default_plugins
from jsb.utils.locking import lockdec
from exit import globalshutdown
from jsb.utils.generic import splittxt, toenc, fromenc, waitforqueue, strippedtxt, waitevents
from jsb.utils.trace import whichmodule
from fleet import getfleet
from aliases import getaliases
from jsb.utils.name import stripname
from tick import tickloop
from threads import start_new_thread, threaded
from morphs import inputmorphs, outputmorphs
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
        if not botname and cfg and cfg.botname: botname = cfg.botname
        if botname: self.botname = botname
        else: self.botname = u"default-%s" % str(type(self)).split('.')[-1][:-2]
        logging.info("botbase - name is %s" % self.botname)
        self.fleetdir = u'fleet' + os.sep + stripname(self.botname)
        if cfg: self.cfg = Config(self.fleetdir + os.sep + u'config', input=cfg)
        else: self.cfg = Config(self.fleetdir + os.sep + u'config')
        LazyDict.__init__(self)
        self.update(self.cfg)
        self.ignore = []
        self.aliases = getaliases()
        self.curevent = None
        self.inqueue = Queue.Queue()
        self.outqueue = Queue.Queue()
        self.reconnectcount = 0
        self.stopped = False
        self.plugs = coreplugs
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
        from jsb.lib.datadir import getdatadir
        datadir = getdatadir()
        self.datadir = datadir + os.sep + self.fleetdir
        self.name = self.botname
        self.owner = self.cfg.owner
        if not self.owner:
            logging.debug(u"owner is not set in %s - using mainconfig" % self.cfg.cfile)
            self.owner = Config().owner
        self.setusers(usersin)
        logging.info(u"botbase - owner is %s" % self.owner)
        self.users.make_owner(self.owner)
        self.outcache = outcache
        self.userhosts = {}
        self.connectok = threading.Event()
        if not self.nick: self.nick = (nick or self.cfg.nick or u'jsb')
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
        self.cmndperms = getcmndperms()
        self.outputmorphs = outputmorphs
        self.inputmorphs = inputmorphs
        fleet = getfleet(datadir)
        if not fleet.byname(self.name): fleet.bots.append(self) ; 
        if not self.isgae:
            defaultrunner.start()
            tickloop.start(self)

    def __deepcopy__(self, a):
        """ deepcopy an event. """  
        logging.debug("botbase - cpy - %s" % type(self))
        bot = BotBase() 
        bot.copyin(self)
        return bot

    def copyin(self, data):
        self.update(data)

    def _resumedata(self):
       """ overload this. """ 
       pass

    def enable(self, modname):
        """ enable plugin given its modulename. """
        try: self.cfg.blacklist and self.cfg.blacklist.remove(modname)
        except ValueError: pass           
        if self.cfg.loadlist and modname not in self.cfg.loadlist: self.cfg.loadlist.append(modname)
        self.cfg.save()

    def disable(self, modname):
        """ disable plugin given its modulename. """
        if self.cfg.blacklist and modname not in self.cfg.blacklist: self.cfg.blacklist.append(modname)
        if self.cfg.loadlist and modname in self.cfg.loadlist: self.cfg.loadlist.remove(modname)
        self.cfg.save()

    def put(self, event):
        """ put an event on the worker queue. """
        if self.isgae:
            from jsb.lib.gae.tasks import start_botevent
            start_botevent(self, event, event.speed)
        else: self.inqueue.put_nowait(event)

    def broadcast(self, txt):
        """ broadcast txt to all joined channels. """
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
        import jsb.lib.users as u
        if not u.users: u.users_boot()
        self.users = u.users

    def loadplugs(self, packagelist=[]):
        """ load plugins from packagelist. """
        self.plugs.loadall(packagelist)
        return self.plugs

    def joinchannels(self):
        """ join channels. """
        time.sleep(Config().waitforjoin or 5)
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
                self.connectok.wait(120)
                if self.connectok.isSet():
                    logging.warn('%s - logged on !' % self.name)
                    start_new_thread(self.joinchannels, ())
                else: logging.warn("%s - failed to logon - connectok is not set" % self.name)
        self.status == "running"
        self.dostart(self.botname, self.type)

    def doremote(self, event):
        """ dispatch an event. """
        if not event: raise NoEventProvided()
        event.forwarded = True
        logging.info("======== start handling REMOTE event ========")
        event.prepare(self)
        self.status = "callback"
        starttime = time.time()
        msg = "%s - %s - %s - %s" % (self.name, event.auth, event.how, event.cbtype)
        if event.how == "background": logging.debug(msg)
        else: logging.info(msg)
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
        logging.info("======== start handling REMOTE event ========")
        return

    #@locked
    def doevent(self, event):
        """ dispatch an event. """
        if not event: raise NoEventProvided()
        if event.isremote(): self.doremote(event) ; return
        event.txt = self.inputmorphs.do(fromenc(event.txt, self.encoding))
        msg = "%s - %s - %s - %s" % (self.name, event.auth, event.how, event.cbtype)
        if event.cbtype in ['NOTICE']: logging.warn("%s - %s - %s" % (self.name, event.nick, event.txt))
        else:
            try:
                int(event.cbtype)
                logging.debug("======== start handling local event ========")
                logging.debug(msg)
            except (ValueError, TypeError):
                if event.cbtype in ['PING', 'PRESENCE'] or event.how == "background": 
                    logging.debug("======== start handling local event ========")
                    logging.debug(msg)
                else: logging.info("======== start handling local event ========") ; logging.info(msg)
        logging.debug(event.dump())
        event.prepare(self)
        self.status = "callback"
        starttime = time.time()
        if self.closed:
            if self.gatekeeper.isblocked(event.origin): return
        if event.status == "done":
            logging.debug("%s - event is done .. ignoring" % self.name)
            return
        self.reloadcheck(event)
        if event.msg or event.isdcc: event.speed = 2
        e1 = cpy(event)
        first_callbacks.check(self, e1)
        if not e1.stop: 
            callbacks.check(self, e1)
            if not e1.stop: last_callbacks.check(self, e1)
        event.callbackdone = True
        return event

    def ownercheck(self, userhost):
        """ check if provided userhost belongs to an owner. """
        if self.cfg and self.cfg.owner:
            if userhost in self.cfg.owner: return True
        return False

    def exit(self, stop=True):
        """ exit the bot. """ 
        logging.warn("%s - exit" % self.name)
        if not self.stopped: self.quit()
        if stop:
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
        logging.debug(u"%s - out - %s" % (self.name, txt))
        print txt

    def makeoutput(self, printto, txt, result=[], nr=375, extend=0, dot=", ", origin=None, *args, **kwargs):
        if not txt: return ""
        txt = self.makeresponse(txt, result, dot)
        res1, nritems = self.less(origin or printto, txt, nr+extend)
        return self.outputmorphs.do(res1)

    def out(self, printto, txt, how="msg", event=None, origin=None, html=False, *args, **kwargs):
        self.outnocb(printto, txt, how, event=event, origin=origin, html=html, *args, **kwargs)
        self.outmonitor(origin, printto, txt, event=event)

    write = out

    def outnocb(self, printto, txt, how="msg", event=None, origin=None, html=False, *args, **kwargs):
        self._raw(txt)

    writenocb = outnocb

    def say(self, channel, txt, result=[], how="msg", event=None, nr=375, extend=0, dot=", ", *args, **kwargs):
        if event and event.userhost in self.ignore: logging.warn("%s - ignore on %s - no output done" % (self.name, event.userhost)) ; return
        if event and event.nooutput:
            logging.debug("%s - event has nooutput set, not outputing" % self.name)
            if event: event.outqueue.put_nowait(txt)
            return
        if event and event.how == "msg":
             if self.type == "irc": target = event.nick
             else: target = channel
        else: target = channel
        if event and event.showall: txt = self.makeresponse(txt, result, dot, *args, **kwargs)
        else: txt = self.makeoutput(channel, txt, result, nr, extend, dot, origin=target, *args, **kwargs)
        if txt: self.out(target, txt, how, event=event, origin=target, *args, **kwargs)
        if event: event.result.append(txt) ; event.resqueue.put_nowait(txt) ; event.outqueue.put_nowait(txt)

    def saynocb(self, channel, txt, result=[], how="msg", event=None, nr=375, extend=0, dot=", ", *args, **kwargs):
        txt = self.makeoutput(channel, txt, result, nr, extend, dot, *args, **kwargs)
        if txt: self.outnocb(channel, txt, how, event=event, origin=channel, *args, **kwargs)

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
            logging.info("addding %s lines to %s outputcache" % (len(txtlist), printto))
            outcache.set(u"%s-%s" % (self.name, printto), txtlist[1:])
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
        dres = []
        if type(txt) == types.DictType or type(txt) == types.ListType:
            result = txt
        if type(result) == types.DictType:
            for key, value in result.iteritems():
                dres.append(u"%s: %s" % (key, unicode(value)))
        if dres: target = dres
        else: target = result
        if target:
            txt = u"<b>" + txt + u"</b>"
            for i in target:
                if not i: continue
                if type(i) == types.ListType or type(i) == types.TupleType:
                    try:
                        res.append(dot.join(i))
                    except TypeError: res.extend(i)
                elif type(i) == types.DictType:
                    for key, value in i.iteritems():
                        res.append(u"%s: %s" % (key, unicode(value)))
                else: res.append(unicode(i))
        if txt: ret = unicode(txt) + dot.join(res)   
        elif res: ret =  dot.join(res)
        if ret: return ret
        return ""
    
    def reloadcheck(self, event):
        """ check if plugin need to be reloaded for callback, """
        plugloaded = []
        target = event.cbtype or event.cmnd
        try:
            from boot import getcallbacktable   
            p = getcallbacktable()[target]
        except KeyError:
            logging.debug("botbase - can't find plugin to reload for %s" % event.cmnd)
            return
        logging.debug("%s - checking %s" % (self.name, unicode(p)))
        for name in p:
            if name in self.plugs: continue
            if name in default_plugins: pass
            elif self.cfg.blacklist and name in self.cfg.blacklist: continue
            elif self.cfg.loadlist and name not in self.cfg.loadlist: continue
            logging.warn("%s - on demand reloading of %s" % (self.name, name))
            try:
                mod = self.plugs.reload(name, force=True, showerror=False)
                if mod: plugloaded.append(mod) ; continue
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
        txt = txt.replace("\003", '')
        txt = txt.replace("\002", "")
        #txt = txt.replace("<b>", "\002")
        #txt = txt.replace("</b>", "\002")
        #txt = txt.replace("<i>", "")
        #txt = txt.replace("</i>", "")
        #txt = txt.replace("&lt;b&gt;", "\002")
        #txt = txt.replace("&lt;/b&gt;", "\002")
        #txt = txt.replace("&lt;i&gt;", "")
        #txt = txt.replace("&lt;/i&gt;", "")
        #txt = txt.replace("&lt;h2&gt;", "\002")
        #txt = txt.replace("&lt;/h2&gt;", "\002")
        #txt = txt.replace("&lt;h3&gt;", "\002")
        #txt = txt.replace("&lt;/h3&gt;", "\002")
        #txt = txt.replace("&lt;li&gt;", "\002")
        #txt = txt.replace("&lt;/li&gt;", "\002")
        return txt

    def dostart(self, botname=None, bottype=None, *args, **kwargs):
        """ create an START event and send it to callbacks. """
        e = EventBase()
        e.bot = self
        e.botname = botname or self.name
        e.bottype = bottype or self.type
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
        logging.debug("%s - START event send to callbacks" % botname)

    def outmonitor(self, origin, channel, txt, event=None):
        """ create an OUTPUT event with provided txt and send it to callbacks. """
        if event: e = cpy(event)
        else: e = EventBase()
        if e.status == "done":
            logging.debug("%s - outmonitor - event is done .. ignoring" % self.name)
            return
        e.bot = self
        e.origin = origin
        e.ruserhost = self.botname +'@' + self.uuid
        e.userhost = e.ruserhost
        e.auth = e.userhost
        e.channel = channel
        e.origtxt = txt
        e.txt = txt
        e.cbtype = 'OUTPUT'
        e.botoutput = True
        e.nodispatch = True
        e.ttl = 1
        e.nick = self.nick or self.botname
        e.bind(self)
        first_callbacks.check(self, e)

    def docmnd(self, origin, channel, txt, event=None, wait=0, showall=False, nooutput=False):
        """ do a command. """
        if event: e = cpy(event)
        else: e = EventBase()
        e.cbtype = "CMND"
        e.bot = self
        e.origin = origin
        e.ruserhost = origin
        e.auth = origin
        e.userhost = origin
        e.channel = channel
        e.txt = unicode(txt)
        e.nick = e.userhost.split('@')[0]
        e.usercmnd = e.txt.split()[0]
        #e.iscommand = True
        #e.iscallback = False
        e.allowqueues = True
        e.onlyqueues = False
        e.closequeue = True
        e.showall = showall
        e.nooutput = nooutput
        e.bind(self)
        #if wait: e.direct = True ; e.nothreads = True ; e.wait = wait
        if cmnds.woulddispatch(self, e) or e.txt[0] == "?": return self.doevent(e)
        #self.put(e)
        #return e

    def putevent(self, origin, channel, txt, event=None, wait=0, showall=False, nooutput=False):
        """ insert an event into the callbacks chain. """
        assert origin
        if event: e = cpy(event)
        else: e = EventBase()
        e.cbtype = "CMND"
        e.bot = self
        e.origin = origin
        e.ruserhost = origin
        e.auth = origin
        e.userhost = origin
        e.channel = channel
        e.txt = unicode(txt)
        e.nick = e.userhost.split('@')[0]
        e.usercmnd = e.txt.split()[0]
        #e.iscommand = True
        #e.iscallback = False
        e.allowqueues = True
        e.onlyqueues = False
        e.closequeue = True
        e.showall = showall
        e.nooutput = nooutput
        e.wait = wait
        e.bind(self)
        self.put(e)
        return e

    def execstr(self, origin, channel, txt, event=None, wait=0, showall=False, nooutput=False):
        e = self.putevent(origin, channel, txt, event, wait, showall, nooutput)
        waitevents([e, ])
        return e.result
