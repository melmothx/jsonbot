# gozerlib/botbase.py
#
#

""" base class for all bots. """

## lib imports

from utils.lazydict import LazyDict
from plugins import plugs as coreplugs
from callbacks import callbacks, gn_callbacks
from eventbase import EventBase
from errors import NoSuchCommand, PlugsNotConnected, NoOwnerSet
from datadir import datadir
from commands import Commands
from config import cfg as mainconfig
from utils.pdod import Pdod
from less import Less
from boot import boot

## basic imports

import time
import logging
import copy
import sys
import getpass
import os

## define

cpy = copy.deepcopy

## classes

class BotBase(LazyDict):

    def __init__(self, cfg=None, usersin=None, plugs=None, jid=None, *args, **kwargs):
        LazyDict.__init__(self)
        self.starttime = time.time()
        self.type = "base"

        if cfg:
            self.cfg = cfg
            self.update(cfg)
        else:
            self.cfg = mainconfig

        self.owner = self.cfg.owner
        if not self.owner:
            logging.warn("owner is not set in %s" % self.cfg.cfile)

        self.setusers(usersin)
        self.users.make_owner(self.owner)
        self.plugs = plugs or coreplugs 

        if jid:
            self.jid = jid
        else:
            self.jid = "default"

        # set datadir to datadir/fleet/<botname>
        self.fleetdir = 'fleet' + os.sep + self.jid
        self.datadir = datadir + os.sep + self.fleetdir
        self.outcache = Less(1)

        try:
            if not os.isdir(self.datadir):
               os.mkdir(self.datadir)
        except:
            pass

        #if not self.cfg:
        #    self.cfg = Config(self.fleetdir + os.sep + 'config')
        #    self.update(self.cfg)


    def setstate(self, state=None):
        self.state = state or Pdod(self.datadir + os.sep + 'state')
        if self.state and not 'joinedchannels' in self.state.data:
            self.state.data.joinedchannels = []

    def setusers(self, users=None):
        if users:
            self.users = users
            return
        import gozerlib.users as u
        if not u.users:
            u.users_boot()
            self.users = u.users
        else:
            self.users = u.users

    def loadplugs(self, dirlist):
        self.plugs.loadall(dirlist)
        return self.plugs

    def start(self):
        while 1: 
            sys.stdout.write("> ")
            try:
                input = sys.stdin.readline()
            except KeyboardInterrupt:
                print "\nbye!"
                os._exit(0)

            if input:
                event = EventBase()
                event.auth = getpass.getuser()
                event.userhost = event.auth
                event.txt = input
                event.usercmnd = input.split()[0]
                event.makeargs()

                try:
                    result = self.plugs.dispatch(self, event)
                except NoSuchCommand:
                    print "no such command: %s" % event.usercmnd


    def doevent(self, event):
        """  dispatch an event. """
        self.curevent = event
        if self.cfg:
            cc = self.cfg.cc or "!"
        else:
            cc = "!"
        if event.txt and event.txt.startswith(cc):
            event.txt = event.txt[1:]
            event.usercmnd = event.txt.split()[0]

        e = cpy(event)
        if event.isremote:
            logging.debug('doing REMOTE callback')
            gn_callbacks.check(self, e)
        else:
            callbacks.check(self, e)

        if event.isremote and not event.remotecmnd:
            logging.debug("event is remote but not command .. not dispatching")
            return

        try:
            return self.plugs.dispatch(self, event)
        except NoSuchCommand:
            event.reply("no such command: %s" % event.usercmnd)

    def ownercheck(self, userhost):
        """ check if provided userhost belongs to an owner. """
        if 'owner' in self:
            if userhost in self.owner:
                return True

        return False

    def _raw(self, txt):
        """ override this. """ 
        sys.stdout.write(u"> %s\n"  % unicode(txt))

    def say(self, channel, txt, result=[], event=None, *args, **kwargs):
        """ override this. """ 
        print u"> " + txt + u', '.join(result)

    def outmonitor(self, origin, channel, txt, event=None):
        """ create an OUTPUT event with provided txt and send it to callbacks. """
        e = EventBase()
        if event:
            e.copyin(event)
        e.origin = origin
        e.ruserhost = event.userhost
        e.userhost = self.name
        e.channel = channel
        e.txt = txt
        e.cbtype = 'OUTPUT'
        callbacks.check(self, e)

    def docmnd(self, origin, channel, txt, event=None):
        """ do a command. """
        e = EventBase()
        if event:
            e.copyin(event)
        e.bot = self
        e.origin = origin
        e.ruserhost = origin
        e.auth = origin
        e.userhost = origin
        e.channel = channel
        e.txt = txt
        e.usercmnd = e.txt.split()[0]
        e.cbtype = 'DOCMND'
        e.makeargs()

        if self.plugs:
            result = self.plugs.dispatch(self, e)
            logging.info("bot - got result - %s" % result)
            return result
        else:
            raise PlugsNotConnected()

    def less(self, who, what, nr=365):
        """ split up in parts of <nr> chars overflowing on word boundaries. """
        what = what.strip()
        txtlist = splittxt(what, nr)
        size = 0

        # send first block
        res = txtlist[0]

        # see if we need to store output in less cache
        result = ""
        if len(txtlist) > 2:
            logging.warn("addding %s lines to %s outputcache" % (len(txtlist), who))
            self.outcache.add(who, txtlist[1:])
            size = len(txtlist) - 2
            result = txtlist[1:2][0]
            if size:
                result += " (+%s)" % size
        else:
            if len(txtlist) == 2:
                result = txtlist[1]

        return [res, result]

    def join(self, *args, **kwargs):
        pass

    def part(self, *args, **kwargs):
        pass

    def action(self, *args, **kwargs):
        pass

    def reconnect(self, *args, **kwargs):
        pass

    def donick(self, *args, **kwargs):
        pass

    def shutdown(self, *args, **kwargs):
        pass

    def quit(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        pass

    def names(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        if self.state:
            self.state.save()
