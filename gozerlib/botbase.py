# gozerlib/botbase.py
#
#

""" base class for all bots. """

## gozerlib imports

from utils.exception import handle_exception
from runner import defaultrunner, cmndrunner, longrunner
from eventhandler import mainhandler
from utils.lazydict import LazyDict
from plugins import plugs as coreplugs
from callbacks import callbacks, first_callbacks, last_callbacks
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
from utils.generic import splittxt, toenc, fromenc, waitforqueue
from utils.trace import whichmodule
from fleet import fleet
from utils.name import stripname
from tick import tickloop
from threads import start_new_thread, threaded

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

## define

cpy = copy.deepcopy

reconnectlock = threading.RLock()
reconnectlocked = lockdec(reconnectlock)

## classes

class BotBase(LazyDict):

    def __init__(self, cfg=None, usersin=None, plugs=None, botname=None, *args, **kwargs):
        self.inqueue = Queue.Queue()
        self.reconnectcount = 0
        self.stopped = False
        self.plugs = plugs or coreplugs
        if not botname and cfg: botname = cfg.botname
        if botname: self.botname = botname
        else: self.botname = u"default-%s" % str(type(self)).split('.')[-1][:-2]
        logging.warn("botbase - name is %s" % self.botname)
        self.fleetdir = u'fleet' + os.sep + stripname(self.botname)
        if cfg: self.update(cfg)
        self.cfg = cfg or Config(self.fleetdir + os.sep + u'config')
        LazyDict.__init__(self)
        try:
            import waveapi
            self.isgae = True
            logging.info("botbase - bot is a GAE bot (%s)" % self.botname)
        except ImportError:
            self.isgae = False
            logging.info("botbase - bot is a shell bot (%s)" % self.botname)
        self.starttime = time.time()
        self.type = "base"
        self.status = "init"
        self.networkname = self.cfg.networkname or self.botname or ""
        if not self.uuid:
            if self.cfg and self.cfg.uuid: self.uuid = self.cfg.uuid
            else:
                self.uuid = self.cfg.uuid = uuid.uuid4()
                self.cfg.save()
        self.datadir = datadir + os.sep + self.fleetdir
        self.name = self.botname
        self.owner = self.cfg.owner
        if not self.owner:
            logging.info(u"owner is not set in %s - using mainconfig" % self.cfg.cfile)
            from config import cfg as mainconfig
            self.owner = mainconfig.owner
        self.setusers(usersin)
        logging.info(u"botbase - owner is %s" % self.owner)
        self.users.make_owner(self.owner)
        self.outcache = Less(3)
        self.userhosts = {}
        self.connectok = threading.Event()
        if not self.nick: self.nick = u'jsonbot'
        try:
            if not os.isdir(self.datadir): os.mkdir(self.datadir)
        except:
            pass
        self.setstate()
        if not fleet.byname(self.name):
            fleet.bots.append(self)
        if not self.isgae:
            defaultrunner.start()
            cmndrunner.start()
            longrunner.start()
            tickloop.start(self)

    def put(self, event):
        self.inqueue.put_nowait(event)

    def _inputloop(self):
        """ fetch events from the inqueue and handle them. """
        logging.warn("%s - inputloop started" % self.name)
        while not self.stopped:
            event = self.inqueue.get()
            if not event:
                break
            self.doevent(event)
        logging.warn("%s - inputloop stopped" % self.name)

    def setstate(self, state=None):
        """ set state on the bot. """
        self.state = state or Pdod(self.datadir + os.sep + 'state')
        if self.state and not 'joinedchannels' in self.state.data:
            self.state.data.joinedchannels = []

    def setusers(self, users=None):
        """ set users on the bot. """
        if users:
            self.users = users
            return
        # initialize users 
        import gozerlib.users as u
        if not u.users: u.users_boot()
        self.users = u.users

    def loadplugs(self, packagelist=[]):
        """ load plugins from packagelist. """
        self.plugs.loadall(packagelist)
        return self.plugs

    def joinchannels(self):
        pass

    def start(self, connect=True):
        """ start the mainloop of the bot. """
        if not self.isgae: start_new_thread(self._inputloop, ())
        if connect:
            self.connect()
            start_new_thread(self.joinchannels, ())
        self.status == "running"
        self.dostart(self.botname, self.type)

    def doevent(self, event):
        """ dispatch an event. """
        if not event: raise NoEventProvided()
        if event.status == "done":
            logging.debug("%s - event is done .. ignoring" % self.name)
            return
        if event.msg or event.isdcc: event.speed = 2
        self.status = "callback"
        starttime = time.time()
        event.prepare()
        msg = "botbase - handling %s - %s" % (event.cbtype, event.auth)
        logging.warn(msg)
        e1 = cpy(event)
        e2 = cpy(event)
        e3 = cpy(event)
        first_callbacks.check(self, e1)
        callbacks.check(self, e2)
        last_callbacks.check(self, e3)
        event.callbackdone = True

    def ownercheck(self, userhost):
        """ check if provided userhost belongs to an owner. """
        if self.cfg and self.cfg.owner:
            if userhost in self.cfg.owner: return True
        return False

    def exit(self):
        """ exit the bot. """ 
        logging.warn("%s - exit" % self.name)
        self.stopped = True   
        self.stopreadloop = True  
        self.connected = False
        self.put(None)
        self.quit()
        time.sleep(1)
        self.shutdown()
        self.stopped = True
        self.save()

    def _raw(self, txt):
        """ override this. """ 
        print txt
        return self

    def out(self, printto, txt, event=None, origin=None, groupchat=None):
        pass

    def outnocb(self, printto, txt, event=None, origin=None, groupchat=None):
        pass

    def say(self, channel, txt, result=[], event=None, *args, **kwargs):
        self._raw(self.makeresponse(txt, result))
        return self

    def saynocb(self, channel, txt, result=[], event=None, *args, **kwargs):
        self._raw(self.makeresponse(txt, result))
        return self

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
        e.origtxt = time.time()
        e.txt = e.origtxt
        e.cbtype = 'START'
        e.botoutput = False
        e.iscmnd = False
        e.ttl = 1
        e.nick = self.nick or self.botname
        callbacks.check(self, e)
        logging.debug("botbase - START event (%s) send to callbacks" % botname)

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
        e.iscmnd = False
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
        e.prepare()
        try:
            event = self.plugs.dispatch(self, e, wait=wait)
            return event
        except NoSuchCommand:
            e.reply("no such command: %s" % e.usercmnd)

    def less(self, who, what, nr=365):
        """ split up in parts of <nr> chars overflowing on word boundaries. """
        if type(what) == types.ListType: txtlist = what
        else:
            what = what.strip()
            txtlist = splittxt(what, nr)
        size = 0
        if not txtlist:
            logging.debug("%s - can't split txt from %s" % (self.name, what))
            return ["", ""]
        res = txtlist[0]
        size = len(txtlist) - 1
        result = ""
        if len(txtlist) > 1:
            logging.debug("%s - addding %s lines to %s outputcache" % (self.name, len(txtlist), who))
            self.outcache.add(who, txtlist[1:])
        return [res, size]

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
            self.exit()
            self.reconnectcount += 1
            logging.warn('%s - reconnecting .. sleeping %s seconds' % (self.name, self.reconnectcount*15))
            time.sleep(self.reconnectcount * 15)   
            self.doreconnect()
        except Exception, ex: 
            handle_exception()

    def doreconnect(self):
        self.start()

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
        if self.state:
            self.state.save()

    def makeresponse(self, txt, result=[], dot=", ", *args, **kwargs):
        """ create a response from a string and result list. """
        res = []
        # check if there are list in list

        if result:
            for i in result:
                if type(i) == types.ListType or type(i) == types.TupleType:
                    try:
                        res.append(dot.join(i))
                    except TypeError:
                        res.extend(i)
                else:   
                    res.append(i)

        if txt: 
            return unicode(txt) + dot.join(res)   
        elif result:
            return dot.join(res)
        return ""   

    