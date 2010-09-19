# gozerlib/socklib/irc/bot.py
# 
#
#

"""
    a bot object handles the dispatching of commands and check for callbacks
    that need to be fired.

"""

## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.utils.generic import waitforqueue, uniqlist, strippedtxt
from gozerlib.commands import cmnds
from gozerlib.callbacks import callbacks
from gozerlib.plugins import plugs as plugins
from gozerlib.datadir import datadir
from gozerlib.threads import start_new_thread, threaded
from gozerlib.utils.dol import Dol
from gozerlib.utils.pdod import Pdod
from gozerlib.persiststate import PersistState
from gozerlib.errors import NoSuchCommand
from gozerlib.channelbase import ChannelBase
from gozerlib.exit import globalshutdown
from gozerlib.botbase import BotBase

## gozerlib.socklib.irc imports

from gozerlib.socklib.partyline import partyline

from channels import Channels
from irc import Irc
from ircevent import IrcEvent
from gozerlib.socklib.wait import Privwait
from gozerlib.socklib.utils.generic import getlistensocket, checkchan, makeargrest

## basic imports

import re
import socket
import struct
import Queue
import time
import os
import types
import logging

## defines

dccchatre = re.compile('\001DCC CHAT CHAT (\S+) (\d+)\001', re.I)

## classes

class IRCBot(Irc):

    """ class that dispatches commands and checks for callbacks to fire. """ 

    def __init__(self, cfg={}, users=None, plugs=None, *args, **kwargs):
        Irc.__init__(self, cfg, users, plugs, *args, **kwargs)
        self.privwait = Privwait()
        if self.state:
            if not self.state.has_key('opchan'): self.state['opchan'] = []
        if not self.state.has_key('joinedchannels'): self.state['joinedchannels'] = []

    def _resume(self, data, reto=None):
        """ resume the bot. """
        if not Irc._resume(self, data, reto): return 0
        for channel in self.state['joinedchannels']: self.who(channel)
        return 1

    def _dccresume(self, sock, nick, userhost, channel=None):
        """ resume dcc loop. """
        if not nick or not userhost: return
        start_new_thread(self._dccloop, (sock, nick, userhost, channel))

    def _dcclisten(self, nick, userhost, channel):
        """ accept dcc chat requests. """
        try:
            listenip = socket.gethostbyname(socket.gethostname())
            (port, listensock) = getlistensocket(listenip)
            ipip2 = socket.inet_aton(listenip)
            ipip = struct.unpack('>L', ipip2)[0]
            chatmsg = 'DCC CHAT CHAT %s %s' % (ipip, port)
            self.ctcp(nick, chatmsg)
            self.sock = sock = listensock.accept()[0]
        except Exception, ex:
            handle_exception()
            logging.error('%s - dcc error: %s' % (self.name, str(ex)))
            return
        self._dodcc(sock, nick, userhost, channel)

    def _dodcc(self, sock, nick, userhost, channel=None):
        """ send welcome message and loop for dcc commands. """
        if not nick or not userhost: return
        try:
            sock.send('Welcome to the GOZERBOT partyline ' + nick + " ;]\n")
            partylist = partyline.list_nicks()
            if partylist: sock.send("people on the partyline: %s\n" % ' .. '.join(partylist))
            sock.send("control character is ! .. bot broadcast is @\n")
        except Exception, ex:
            handle_exception()
            logging.error('%s - dcc error: %s' % (self.name, str(ex)))
            return
        start_new_thread(self._dccloop, (sock, nick, userhost, channel))

    def _dccloop(self, sock, nick, userhost, channel=None):

        """ loop for dcc commands. """

        sockfile = sock.makefile('r')
        sock.setblocking(True)
        res = ""
        partyline.add_party(self, sock, nick, userhost, channel)

        while 1:
            time.sleep(0.001)
            try:
                res = sockfile.readline()
                logging.debug("%s - dcc - %s got %s" % (self.name, userhost, res))
                if self.stopped or not res:
                    logging.warn('%s - closing dcc with %s' % (self.name, nick))
                    partyline.del_party(nick)
                    return
            except socket.timeout:
                continue
            except socket.error, ex:
                try:
                    (errno, errstr) = ex
                except:
                    errno = 0
                    errstr = str(ex)
                if errno == 35 or errno == 11:
                    continue
                else:
                    raise
            except Exception, ex:
                handle_exception()
                logging.warn('%s - closing dcc with %s' % (self.name, nick))
                partyline.del_party(nick)
                return
            try:
                res = strippedtxt(res.strip())
                ievent = IrcEvent()
                ievent.printto = sock
                ievent.bottype = "irc"
                ievent.nick = nick
                ievent.userhost = userhost
                ievent.auth = userhost
                ievent.channel = channel or ievent.userhost
                ievent.origtxt = res
                ievent.txt = res
                ievent.cmnd = 'DCC'
                ievent.cbtype = 'DCC'
                ievent.bot = self
                ievent.sock = sock
                ievent.speed = 1
                ievent.isdcc = True
                ievent.msg = True
                ievent.finish()
                logging.debug("%s - dcc - constructed event" % self.name)
                if ievent.txt[0] == "!":
                    self.doevent(ievent)
                    continue
                elif ievent.txt[0] == "@":
                    partyline.say_broadcast_notself(ievent.nick, "[%s] %s" % (ievent.nick, ievent.txt))
                    q = Queue.Queue()
                    ievent.queues = [q]
                    ievent.txt = ievent.txt[1:]
                    self.doevent(ievent)
                    result = waitforqueue(q, 5)
                    if result:
                        for i in result:
                            partyline.say_broadcast("[bot] %s" % i)
                    continue
                else:
                    partyline.say_broadcast_notself(ievent.nick, "[%s] %s" % (ievent.nick, ievent.txt))
                self.privwait.check(ievent)
            except socket.error, ex:
                try:
                    (errno, errstr) = ex
                except:
                    errno = 0
                    errstr = str(ex)
                if errno == 35 or errno == 11:
                    continue
            except Exception, ex:
                handle_exception()
        sockfile.close()
        logging.warn('%s - closing dcc with %s' %  (self.name, nick))

    def _dccconnect(self, nick, userhost, addr, port):
        """ connect to dcc request from nick. """
        try:
            port = int(port)
            logging.warn("%s - dcc - connecting to %s:%s (%s)" % (self.name, addr, port, userhost))
            if re.search(':', addr):
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.connect((addr, port))
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((addr, port))
        except Exception, ex:
            logging.error('%s - dcc error: %s' % (self.name, str(ex)))
            return
        self._dodcc(sock, nick, userhost, userhost)

    def broadcast(self, txt):
        """ broadcast txt to all joined channels. """
        for i in self.state['joinedchannels']: self.say(i, txt)

    def getchannelmode(self, channel):
        """ send MODE request for channel. """
        if not channel:
            return
        self.putonqueue(9, None, 'MODE %s' % channel)

    def join(self, channel, password=None):
        """ join a channel .. use optional password. """
        result = Irc.join(self, channel, password)
        if result != 1:
            return result
        chan = ChannelBase(channel)
        got = False
        if password:
            chan.setkey('IRC',password)
            got = True
        if not chan.data.cc:
            chan.data.cc = self.cfg.defaultcc or '!'
            got = True
        if not chan.data.perms:
            chan.data.perms = []
            got = True
        if not chan.data.mode:
            chan.data.mode = ""
            got = True
        if got:
            chan.save()
        self.getchannelmode(channel)
        return 1

    def handle_privmsg(self, ievent):
        """ check if PRIVMSG is command, if so dispatch. """
        if ievent.nick in self.nicks401:
            logging.debug("%s - %s is available again" % (self.name, ievent.nick))
            self.nicks401.remove(ievent.nick)
        if not ievent.txt: return
        chat = re.search(dccchatre, ievent.txt)
        if chat:
            if self.users.allowed(ievent.userhost, 'USER'):
                start_new_thread(self._dccconnect, (ievent.nick, ievent.userhost, chat.group(1), chat.group(2))) 
                return
        if '\001' in ievent.txt:
            Irc.handle_privmsg(self, ievent)
            return
        ievent.bot = self
        ievent.sock = self.sock
        chan = ievent.channel
        if chan == self.nick:
            ievent.msg = 1
            ievent.speed =  4
            ievent.printto = ievent.nick
            ccs = ['!', '@', self.cfg['defaultcc']]
            self.privwait.check(ievent)
            if ievent.isresponse:
                return
            if self.cfg['noccinmsg'] and self.msg:
                self.put(ievent)
            elif ievent.txt[0] in ccs: 
                self.put(ievent)
            return
        self.put(ievent)
        if not ievent.iscmnd(): self.privwait.check(ievent)

    def handle_join(self, ievent):
        """ handle joins. """
        if ievent.nick in self.nicks401:
             logging.debug("%s - %s is available again" % (self.name, ievent.nick))
             self.nicks401.remove(ievent.nick)
        chan = ievent.channel
        nick = ievent.nick
        if nick == self.nick:
            logging.warn("%s - joined %s" % (self.name, ievent.channel))
            time.sleep(0.5)
            self.who(chan)
            return
        logging.info("%s - %s joined %s" % (self.name, ievent.nick, ievent.channel))
        self.userhosts[nick] = ievent.userhost

    def handle_kick(self, ievent):
        """ handle kick event. """
        try:
            who = ievent.arguments[1]
        except IndexError:
            return
        chan = ievent.channel
        if who == self.nick:
            if chan in self.state['joinedchannels']:
                self.state['joinedchannels'].remove(chan)
                self.state.save()

    def handle_nick(self, ievent):
        """ update userhost cache on nick change. """
        nick = ievent.txt
        self.userhosts[nick] = ievent.userhost
        if ievent.nick == self.nick or ievent.nick == self.orignick:
            self.cfg['nick'] = nick
            self.cfg.save()

    def handle_part(self, ievent):
        """ handle parts. """
        chan = ievent.channel
        if ievent.nick == self.nick:
            logging.warn('%s - parted channel %s' % (self.name, chan))
            if chan in self.state['joinedchannels']:
                self.state['joinedchannels'].remove(chan)
                self.state.save()

    def handle_ievent(self, ievent):
        """ check for callbacks, call Irc method. """
        try:
            Irc.handle_ievent(self, ievent)
            if ievent.cmnd == 'JOIN' or ievent.msg:
                if ievent.nick in self.nicks401: self.nicks401.remove(ievent.nick)
            if ievent.cmnd != "PRIVMSG":
                i = IrcEvent()
                i.copyin(ievent)
                i.bot = self
                i.sock = self.sock
                ievent.nocb = True
                callbacks.check(self, i)
        except:
            handle_exception()
 
    def handle_quit(self, ievent):
        """ check if quit is because of a split. """
        if '*.' in ievent.txt or self.server in ievent.txt: self.splitted.append(ievent.nick)
        
    def handle_mode(self, ievent):
        """ check if mode is about channel if so request channel mode. """
        logging.warn("%s - mode change %s" % (self.name, str(ievent.arguments)))
        try:
            dummy = ievent.arguments[2]
        except IndexError:
            chan = ievent.channel
            self.getchannelmode(chan)
            ievent.chan.mode = ievent.arguments[1]
            ievent.chan.save()

    def handle_311(self, ievent):
        """ handle 311 response .. sync with userhosts cache. """
        target, nick, user, host, dummy = ievent.arguments
        nick = nick
        userhost = "%s@%s" % (user, host)
        logging.debug('%s - adding %s to userhosts: %s' % (self.name, nick, userhost))
        self.userhosts[nick] = userhost

    def handle_352(self, ievent):
        """ handle 352 response .. sync with userhosts cache. """
        args = ievent.arguments
        channel = args[1]  
        nick = args[5]
        user = args[2]
        host = args[3]
        userhost = "%s@%s" % (user, host)
        logging.debug('%s - adding %s to userhosts: %s' % (self.name, nick, userhost))
        self.userhosts[nick] = userhost

    def handle_353(self, ievent):
        """ handle 353 .. check if we are op. """
        userlist = ievent.txt.split()
        chan = ievent.channel
        for i in userlist:
            if i[0] == '@' and i[1:] == self.nick:
                if chan not in self.state['opchan']:
                    self.state['opchan'].append(chan)

    def handle_324(self, ievent):
        """ handle mode request responses. """
        ievent.chan.mode = ievent.arguments[2]
        ievent.chan.save()

    def handle_invite(self, ievent):
        """ join channel if invited by OPER. """
        if self.users and self.users.allowed(ievent.userhost, ['OPER', ]): self.join(ievent.txt)

    def settopic(self, channel, txt):
        """ set topic of channel to txt. """
        if not channel or not txt: return
        self.putonqueue(7, None, 'TOPIC %s :%s' % (channel, txt))

    def gettopic(self, channel):
        """ get topic data. """
        if not channel: return
        queue332 = Queue.Queue()
        queue333 = Queue.Queue()
        self.wait.register('332', channel, queue332)
        self.wait.register('333', channel, queue333)
        self.putonqueue(7, None, 'TOPIC %s' % channel)
        try:
            res = queue332.get(1, 5)
        except Queue.Empty: return None
        what = res.txt
        try:
            res = queue333.get(1, 5)
        except Queue.Empty: return None
        try:
            splitted = res.postfix.split()
            who = splitted[2]
            when = float(splitted[3])
        except (IndexError, ValueError): return None
        return (what, who, when)
