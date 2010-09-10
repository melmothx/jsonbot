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
from ircevent import Ircevent
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
        # object used to wait for PRIVMSG
        self.privwait = Privwait()
        # channels where we are op
        if self.state:
            if not self.state.has_key('opchan'):
                self.state['opchan'] = []
        #self.userchannels = Dol()

        if not self.state.has_key('joinedchannels'):
            self.state['joinedchannels'] = []

    def _resume(self, data, reto=None):

        """ resume the bot. """

        if not Irc._resume(self, data, reto):
            return 0
        for channel in self.state['joinedchannels']:
            self.who(channel)
        return 1

    def _dccresume(self, sock, nick, userhost, channel=None):

        """ resume dcc loop. """

        if not nick or not userhost:
            return
        start_new_thread(self._dccloop, (sock, nick, userhost, channel))

    def _dcclisten(self, nick, userhost, channel):

        """ accept dcc chat requests. """

        try:
            # get listen socket on host were running on
            listenip = socket.gethostbyname(socket.gethostname())
            (port, listensock) = getlistensocket(listenip)
            # convert ascii ip to netwerk 32 bit 
            ipip2 = socket.inet_aton(listenip)
            ipip = struct.unpack('>L', ipip2)[0]
            # send dcc chat request
            chatmsg = 'DCC CHAT CHAT %s %s' % (ipip, port)
            self.ctcp(nick, chatmsg)
            # go listen to response
            self.sock = sock = listensock.accept()[0]
        except Exception, ex:
            handle_exception()
            logging.error('irc - dcc error: %s' % str(ex))
            return

        # connected
        self._dodcc(sock, nick, userhost, channel)

    def _dodcc(self, sock, nick, userhost, channel=None):

        """ send welcome message and loop for dcc commands. """

        if not nick or not userhost:
            return

        try:
            # send welcome message .. show list of commands for USER perms
            sock.send('Welcome to the GOZERBOT partyline ' + nick + " ;]\n")
            partylist = partyline.list_nicks()
            if partylist:
                sock.send("people on the partyline: %s\n" % ' .. '.join(partylist))
            sock.send("control character is ! .. bot broadcast is @\n")
        except Exception, ex:
            handle_exception()
            logging.error('irc - dcc error: %s' % str(ex))
            return
        start_new_thread(self._dccloop, (sock, nick, userhost, channel))

    def _dccloop(self, sock, nick, userhost, channel=None):

        """ loop for dcc commands. """

        sockfile = sock.makefile('r')
        sock.setblocking(True)
        res = ""
        # add joined user to the partyline
        partyline.add_party(self, sock, nick, userhost, channel)

        while 1:
            time.sleep(0.001)
            try:
                # read from socket
                res = sockfile.readline()
                logging.debug("irc - dcc - %s got %s" % (userhost, res))
                # if res == "" than the otherside had disconnected
                if self.stopped or not res:
                    logging.warn('irc - closing dcc with ' + nick)
                    partyline.del_party(nick)
                    return
            except socket.timeout:
                # skip on timeout 
                continue
            except socket.error, ex:
                # handle socket errors .. skip on errno 35 and 11 temp unavail
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
                # other exception occured .. close connection
                handle_exception()
                logging.warn('irc - closing dcc with ' + nick)
                partyline.del_party(nick)
                return
            try:
                # see if user provided channel
                res = strippedtxt(res.strip())
                # create ircevent
                ievent = Ircevent()
                ievent.printto = sock
                ievent.bottype = "irc"
                ievent.nick = nick
                ievent.userhost = userhost
                ievent.auth = userhost
                ievent.channel = channel or ievent.userhost
                ievent.chan = ChannelBase(ievent.channel)
                ievent.origtxt = res
                ievent.txt = res
                ievent.cmnd = 'DCC'
                ievent.bot = self
                ievent.sock = sock
                ievent.speed = 1
                ievent.isdcc = True
                ievent.msg = True
                logging.debug("irc - dcc - constructed event")
                # check if its a command if so dispatch
                if ievent.txt[0] == "!":
                    self.doevent(ievent)
                    continue
                elif ievent.txt[0] == "@":
                    # command is broadcast so send response to the paryline
                    # members
                    partyline.say_broadcast_notself(ievent.nick, "[%s] %s" % (ievent.nick, ievent.txt))
                    # make queue and run trydispatch to see if command has 
                    # fired
                    q = Queue.Queue()
                    ievent.queues = [q]
                    ievent.txt = ievent.txt[1:]
                    self.doevent(ievent)
                    # wait for result .. default timeout is 10 sec
                    result = waitforqueue(q, 5)
                    if result:
                        # broadcast result
                        for i in result:
                            partyline.say_broadcast("[bot] %s" % i)
                    continue
                else:
                    # not a command so send txt to partyline
                    partyline.say_broadcast_notself(ievent.nick, \
"[%s] %s" % (ievent.nick, ievent.txt))
                # check PRIVMSG wait
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
        logging.warn('irc - closing dcc with ' + nick)

    def _dccconnect(self, nick, userhost, addr, port):

        """ connect to dcc request from nick. """

        try:
            port = int(port)
            logging.warn("irc - dcc - connecting to %s:%s (%s)" % (addr, port, userhost))
            if re.search(':', addr):
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.connect((addr, port))
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((addr, port))
        except Exception, ex:
            logging.error('irc - dcc error: %s' % str(ex))
            return

        # were connected .. start dcc loop
        self._dodcc(sock, nick, userhost, userhost)

    @threaded
    def start(self):
        """ start the bot. """
        try:
            Irc.start(self)
        except (socket.gaierror, socket.error), ex:
            logging.error("irc - connect error: %s" % str(ex))
            Irc.reconnect(self)
        except (KeyboardInterrupt, EOFError):
            globalshutdown() 

        BotBase.start(self)

    def joinchannels(self):

        """ join channels. """

        for i in self.state['joinedchannels']:
            try:
                channel = ChannelBase(i)
                if channel:
                    key = channel.getpass()
                else:
                    key=None
                start_new_thread(self.join, (i, key))
                time.sleep(1)
            except Exception, ex:
                logging.warn('irc - failed to join %s: %s' % (i, str(ex)))
                handle_exception()

    def broadcast(self, txt):

        """ broadcast txt to all joined channels. """

        for i in self.state['joinedchannels']:
            self.say(i, txt)

    def save(self):
        """ saves channels and state. """
        Irc.save(self)

    def stop(self):
        """ stop the bot. """
        self.stopped = 1
        # shut down handlers
        logging.warn('irc - stopped')

    def exit(self):
        """ save data, quit the bot and do shutdown. """
        if self.connectok.isSet():
            try:
                self._raw('QUIT :%s' % self.cfg['quitmsg'])
            except IOError:
                pass
        Irc.exit(self)
        self.stop()
        partyline.stop(self)
        self.save()
        logging.warn('irc - exit')
        return 1

    def getchannelmode(self, channel):
        """ send MODE request for channel. """
        if not channel:
            return
        self.putonqueue(9, 'MODE %s' % channel)

    def join(self, channel, password=None):
        """ join a channel .. use optional password. """
        result = Irc.join(self, channel, password)
        if result != 1:
            return result
        chan = ChannelBase(channel)
        # if password is provided set it
        got = False
        if password:
            chan.setkey('IRC',password)
            got = True
        # check for control char .. if its not there init to !
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
            logging.debug("irc - %s is available again" % ievent.nick)
            self.nicks401.remove(ievent.nick)

        if not ievent.txt:
            return

        # check if it is a dcc chat request
        chat = re.search(dccchatre, ievent.txt)
        if chat:
            # check if the user is known
            if self.users.allowed(ievent.userhost, 'USER'):
                # start connection
                start_new_thread(self._dccconnect, (ievent.nick, ievent.userhost, chat.group(1), chat.group(2))) 
                return

        # see if base class method would handle it
        if '\001' in ievent.txt:
            Irc.handle_privmsg(self, ievent)
            return

        # set bot and socket in ircevent
        ievent.bot = self
        ievent.sock = self.sock
        chan = ievent.channel

        # check for /msg
        if chan == self.nick:
            ievent.msg = 1
            ievent.speed =  7
            ievent.printto = ievent.nick
            ccs = ['!', '@', self.cfg['defaultcc']]
            # check for PRIVMSG waiting callback
            self.privwait.check(ievent)
            if ievent.isresponse:
                return
            if self.cfg['noccinmsg'] and self.msg:
                self.doevent(ievent)
            elif ievent.txt[0] in ccs: 
                self.doevent(ievent)
            return

        #ievent.printto = channel

        # see if we can get channel control character

        try:
            channel = ChannelBase(chan)
            cchar = channel.data.cc
        except Exception, ex:
            handle_exception()
            cchar = "!"
        if not cchar:
            cchar = "!"

        self.doevent(ievent)

        if not ievent.iscmnd:
            # check for PRIVMSG waiting callback
            self.privwait.check(ievent)

    def handle_join(self, ievent):

        """ handle joins. """

        if ievent.nick in self.nicks401:
             logging.debug("irc - %s is available again" % ievent.nick)
             self.nicks401.remove(ievent.nick)
        chan = ievent.channel
        nick = ievent.nick

        # see if its the bot who is joining
        if nick == self.nick:
            logging.warn("irc - joined %s" % ievent.channel)
            # check if we already have a channels object, if not init it
            time.sleep(0.5)
            self.who(chan)
            return

        logging.info("%s joined %s" % (ievent.nick, ievent.channel))
        # sync joined user with userhosts cache
        self.userhosts[nick] = ievent.userhost
        #if self.userchannels:
        #    self.userchannels.adduniq(nick, chan)

    def handle_kick(self, ievent):

        """ handle kick event. """

        try:
            who = ievent.arguments[1]
        except IndexError:
            return

        chan = ievent.channel

        # see if its the bot who got kicked .. if so remove from
        # joinedchannels
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

        # see if its the bot who is parting
        if ievent.nick == self.nick:
            logging.warn('irc - parted channel %s' % chan)
            # remove from joinedchannels
            if chan in self.state['joinedchannels']:
                self.state['joinedchannels'].remove(chan)
                self.state.save()

    def handle_ievent(self, ievent):

        """ check for callbacks, call Irc method. """

        try:
            # call parent method
            Irc.handle_ievent(self, ievent)
            # check for callbacks
            if ievent.cmnd == 'JOIN' or ievent.msg:
                if ievent.nick in self.nicks401:
                    self.nicks401.remove(ievent.nick)
            if ievent.cmnd != "PRIVMSG":
                i = Ircevent()
                i.copyin(ievent)
                i.bot = self
                i.sock = self.sock
                ievent.nocb = True
                callbacks.check(self, i)
        except:
            handle_exception()
 
    def handle_quit(self, ievent):

        """ check if quit is because of a split. """

        if '*.' in ievent.txt or self.server in ievent.txt:
            self.splitted.append(ievent.nick)
        
    def handle_mode(self, ievent):

        """ check if mode is about channel if so request channel mode. """

        logging.warn("irc - mode change %s" % str(ievent.arguments))

        try:
            dummy = ievent.arguments[2]
        except IndexError:
            chan = ievent.channel
            # channel mode change has 2 arguments
            self.getchannelmode(chan)
            ievent.chan.mode = ievent.arguments[1]

    def handle_311(self, ievent):

        """ handle 311 response .. sync with userhosts cache. """

        target, nick, user, host, dummy = ievent.arguments
        nick = nick
        userhost = "%s@%s" % (user, host)
        logging.debug('irc - adding %s to userhosts: %s' % (nick, userhost))
        # userhosts cache is accessed by lower case nick
        self.userhosts[nick] = userhost

    def handle_352(self, ievent):

        """ handle 352 response .. sync with userhosts cache. """

        args = ievent.arguments
        channel = args[1]  
        nick = args[5]
        user = args[2]
        host = args[3]
        userhost = "%s@%s" % (user, host)
        logging.debug('adding %s to userhosts: %s' % (nick, userhost))
        self.userhosts[nick] = userhost
        #if self.userchannels:
        #    self.userchannels.adduniq(nick, channel)

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
        #self.channels.set(ievent.channel, 'mode', ievent.arguments[2])

    def handle_invite(self, ievent):

        """ join channel if invited by OPER. """

        if self.users and self.users.allowed(ievent.userhost, ['OPER', ]):
            self.join(ievent.txt)

    def settopic(self, channel, txt):

        """ set topic of channel to txt. """

        if not channel or not txt:
            return
        self.putonqueue(7, 'TOPIC %s :%s' % (channel, txt))

    def gettopic(self, channel):

        """ get topic data. """

        if not channel:
            return

        queue332 = Queue.Queue()
        queue333 = Queue.Queue()
        self.wait.register('332', channel, queue332)
        self.wait.register('333', channel, queue333)
        self.putonqueue(7, 'TOPIC %s' % channel)

        try:
            res = queue332.get(1, 5)
        except Queue.Empty:
            return None

        what = res.txt

        try:
            res = queue333.get(1, 5)
        except Queue.Empty:
            return None

        try:
            splitted = res.postfix.split()
            who = splitted[2]
            when = float(splitted[3])
        except (IndexError, ValueError):
            return None

        return (what, who, when)

