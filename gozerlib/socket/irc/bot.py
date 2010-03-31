# gozerlib/socket/irc/bot.py
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
from gozerlib.users import users
from gozerlib.datadir import datadir
from gozerlib.threads import start_new_thread, threaded
from gozerlib.utils.dol import Dol
from gozerlib.utils.pdod import Pdod
from gozerlib.persiststate import PersistState
from gozerlib.runner import runners_start
from gozerlib.errors import NoSuchCommand
from gozerlib.channelbase import ChannelBase

## gozerlib.socket.irc imports

from gozerlib.socket.partyline import partyline

from channels import Channels
from irc import Irc
from ircevent import Ircevent
from monitor import outmonitor
from wait import Privwait
from gozerlib.socket.utils.generic import getlistensocket, checkchan, makeargrest

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

class Bot(Irc):

    """ class that dispatches commands and checks for callbacks to fire. """ 

    def __init__(self, cfg={}, users=None, plugs=None, *args, **kwargs):
        Irc.__init__(self, cfg, users, plugs, *args, **kwargs)
        # object used to wait for PRIVMSG
        self.privwait = Privwait()
        # channels where we are op
        if self.state:
            if not self.state.has_key('opchan'):
                self.state['opchan'] = []
        self.userchannels = Dol()

        if not self.state.has_key('joinedchannels'):
            self.state['joinedchannels'] = []

        self.monitor = outmonitor
        self.monitor.start()


    def __str__(self):
        return "name: %s nick: %s server: %s ipv6: %s ssl: %s port:%s" % (self.name, \
self.nick, self.server, self.ipv6, self.ssl, self.port)

    def _resume(self, data, reto):

        """ resume the bot. """

        if not Irc._resume(self, data, reto):
            return 0
        for i in self.state['joinedchannels']:
            self.who(self, i)
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
            sock = listensock.accept()[0]
        except Exception, ex:
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
            cmndslist = cmnds.list('USER')
            cmndslist.sort()
            sock.send('Welcome to the GOZERBOT partyline ' + nick + " ;]\n")
            partylist = partyline.list_nicks()
            if partylist:
                sock.send("people on the partyline: %s\n" % ' .. '.join(partylist))
            sock.send("control character is ! .. bot broadcast is @\n")
        except Exception, ex:
            logging.error('irc - dcc error: %s' % str(ex))
            return
        start_new_thread(self._dccloop, (sock, nick, userhost, channel))

    def _dccloop(self, sock, nick, userhost, channel=None):

        """ loop for dcc commands. """

        sockfile = sock.makefile('r')
        res = ""
        # add joined user to the partyline
        partyline.add_party(self, sock, nick, userhost, channel)

        while 1:
            time.sleep(0.001)
            try:
                # read from socket
                res = sockfile.readline()
                # if res == "" than the otherside had disconnected
                if self.stopped or not res:
                    logging.info('irc - closing dcc with ' + nick)
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
                logging.info('irc - closing dcc with ' + nick)
                partyline.del_party(nick)
                return
            try:
                # see if user provided channel
                res = strippedtxt(res.strip())
                chan = checkchan(self, res)
                if chan != None:
                    (channel, res) = chan
                else:
                    channel = nick
                # create ircevent
                ievent = Ircevent()
                ievent.nick = nick
                ievent.userhost = userhost
                ievent.channel = channel
                ievent.origtxt = res
                ievent.txt = res
                ievent.cmnd = 'DCC'
                ievent.bot = self
                ievent.sock = sock
                ievent.speed = 1
                ievent.isdcc = True
                ievent.msg = True
                # check if its a command if so dispatch
                if ievent.txt[0] == "!":
                    ievent.txt = ievent.txt[1:]
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
        self._dodcc(sock, nick, userhost)

    @threaded
    def start(self):
        Irc.start(self)
        self.joinchannels()


    @threaded
    def reconnect(self):

        """ reconnect and if succesfull join channels. """

        if Irc.reconnect(self):
            self.joinchannels()

    def joinchannels(self):

        """ join channels. """

        for i in self.state['joinedchannels']:
            try:
                channel = ChannelBase(self.datadir + os.sep + 'channels' + os.sep + i)
                if channel:
                    key = channel.getpass()
                else:
                    key=None
                logging.warn('irc - join %s' % i.split()[0])
                start_new_thread(self.join, (i, key))
                time.sleep(1)
            except Exception, ex:
                logging.warn('irc - failed to join %s: %s' % (i, str(ex)))
                handle_exception()

    def broadcast(self, txt):

        """ broadcast txt to all joined channels. """

        for i in self.state['joinedchannels']:
            self.say(i, txt)

    def send(self, txt):

        """ call Irc send and check for monitor callbacks. """

        Irc.send(self, str(txt))
        self.monitor.put(self, str(txt))

    def save(self):

        """ saves channels and state. """

        if self.channels:
            self.channels.save()
        if self.userhosts:
            self.userhosts.save()
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
        self.stop()
        partyline.stop(self)
        Irc.exit(self)
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

    def say(self, printto, what, who=None, how='msg', fromm=None, speed=5, groupchat=False):

        """ output what to printto. """

        # check if printto is a queue if so put output to the queue
        if type(printto) == type(Queue.Queue): 
            printto.put_nowait('[%s] %s' % (self.name, what))
            return
        # check if bot is in notice mode
        notice = False
        try:
            notice = self.channels[printto]['notice']
        except (KeyError, TypeError):
            pass
        if notice:
            how = 'notice'
        Irc.say(self, printto, what, who, how, fromm, speed, groupchat)

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
            if users.allowed(ievent.userhost, 'USER'):
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
            if not self.cfg['noccinmsg']:
                self.doevent(ievent)
            elif ievent.txt[0] in ccs: 
                ievent.txt = ievent.txt[1:]
                self.doevent(ievent)
            return

        ievent.printto = chan

        # see if we can get channel control character
        try:
            cchar = self.channels[chan]['cc']
        except LookupError:
            cchar = self.cfg['defaultcc'] or '!'
        except TypeError:
            cchar = self.cfg['defaultcc'] or '!'

        # see if cchar matches, if so dispatch
        ievent.speed = 5
        if ievent.txt[0] in cchar:
            ievent.cc = ievent.txt[0]
            ievent.txt = ievent.txt[1:]
            ievent.usercmnd = ievent.txt.split()[0]
            try:
                self.doevent(ievent)
            except NoSuchCommand:
                ievent.reply("no %s command found" % ievent.usercmnd)

            return

        # see if were adressed, if so dispatch
        txtlist = ievent.txt.split(':', 1)
        if txtlist[0]  == self.nick:
            if len(txtlist) < 2:
                return
            ievent.txt = txtlist[1].strip()
            ievent.usercmnd = ievent.txt.split()[0]
            ievent.makeargs()
            try:
                self.doevent(ievent)
            except NoSuchCommand:
                ievent.reply("no %s command found" % ievent.usercmnd)
            return

        # habbie addressing mode
        txtlist = ievent.txt.split(',', 1)
        if txtlist[0] == self.nick:
            if len(txtlist) < 2:
                return
            ievent.txt = txtlist[1].strip()
            ievent.usercmnd = ievent.txt.split()[0]
            ievent.makeargs()
            try:
                self.doevent(ievent)
            except NoSuchCommand:
                ievent.reply("no %s command found" % ievent.usercmnd)
            return

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
            # check if we already have a channels object, if not init it
            if self.channels:
                if not self.channels.has_key(chan):
                    self.channels[chan] = {}
                    self.channels[chan]['cc'] = self.cfg['defaultcc'] or '!'
                if not chan in self.state['joinedchannels']:
                    self.state['joinedchannels'].append(chan)
                    self.state.save()
                if chan in self.state['opchan']:
                    self.state['opchan'].remove(chan)
                    self.state.save()
                time.sleep(0.5)
                self.who(self, chan)
                return

        # sync joined user with userhosts cache
        if self.userhosts:
            self.userhosts.data[nick] = ievent.userhost
        if self.userchannels:
            self.userchannels.adduniq(nick, chan)

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
        self.userhosts.data[nick] = ievent.userhost

        if ievent.nick == self.nick:
            self.cfg['nick'] = nick
            self.cfg.save()

        try:
            self.userchannels[nick] = self.userchannels[ievent.nick]
        except:
           raise

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
            i = Ircevent()
            i.copyin(ievent)
            i.bot = self
            i.sock = self.sock
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
            self.channels.set(chan, 'mode', ievent.arguments[1])    

    def handle_311(self, ievent):

        """ handle 311 response .. sync with userhosts cache. """

        target, nick, user, host, dummy = ievent.arguments
        nick = nick
        userhost = "%s@%s" % (user, host)
        logging.debug('irc - adding %s to userhosts: %s' % (nick, userhost))
        # userhosts cache is accessed by lower case nick
        if self.userhosts:
            self.userhosts.data[nick] = userhost

    def handle_352(self, ievent):

        """ handle 352 response .. sync with userhosts cache. """

        args = ievent.arguments
        channel = args[1]  
        nick = args[5]
        user = args[2]
        host = args[3]
        userhost = "%s@%s" % (user, host)
        logging.debug('adding %s to userhosts: %s' % (nick, userhost))
        self.userhosts.data[nick] = userhost
        self.userchannels.adduniq(nick, channel)

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

        self.channels.set(ievent.channel, 'mode', ievent.arguments[2])

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

