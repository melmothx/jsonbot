# gozerlib/socklib/irc/irc.py
#
#

""" 
    an Irc object handles the connection to the irc server .. receiving,
    sending, connect and reconnect code.

"""

## gozerlib imports

from gozerlib.utils.exception import handle_exception
from gozerlib.utils.generic import toenc, fromenc
from gozerlib.socklib.utils.generic import getrandomnick, strippedtxt
from gozerlib.socklib.utils.generic import fix_format, splittxt, waitforqueue, uniqlist
from gozerlib.utils.locking import lockdec
from gozerlib.config import cfg as config
from gozerlib.datadir import datadir
from gozerlib.botbase import BotBase
from gozerlib.threads import start_new_thread, threaded
from gozerlib.utils.pdod import Pdod
from gozerlib.channelbase import ChannelBase
from gozerlib.morphs import inputmorphs, outputmorphs
from gozerlib.exit import globalshutdown
from gozerlib.fleet import fleet

## gozerlib.irc imports

from ircevent import Ircevent
from gozerlib.socklib.wait import Wait

## basic imports

import time
import thread
import socket
import threading
import os
import Queue
import random
import logging
import types
import re

## locks

outlock = thread.allocate_lock()
outlocked = lockdec(outlock)

## exceptions

class AlreadyConnected(Exception):

    """ already connected exception """

    pass

class AlreadyConnecting(Exception):

    """ bot is already connecting exception """

    pass

class Irc(BotBase):

    """ the irc class, provides interface to irc related stuff. """

    def __init__(self, cfg=None, users=None, plugs=None, *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, *args, **kwargs)
        BotBase.setstate(self)
        self.type = 'irc'
        self.wait = Wait()
        self.outputlock = thread.allocate_lock()
        self.fsock = None
        self.oldsock = None
        self.sock = None
        if self.cfg:
            if not self.cfg.has_key('nolimiter'):
                self.nolimiter = 0
        else:
            self.nolimiter = self.cfg['nolimiter']
        self.reconnectcount = 0
        self.pongcheck = 0
        self.nickchanged = 0
        self.noauto433 = 0
        if self.state:
            if not self.state.has_key('alternick'):
                self.state['alternick'] = self.cfg['alternick']
            if not self.state.has_key('no-op'):
                self.state['no-op'] = []
        self.nrevents = 0
        self.gcevents = 0
        self.outqueues = [Queue.Queue() for i in range(10)]
        self.tickqueue = Queue.Queue()
        self.nicks401 = []
        self.stopreadloop = False
        self.stopoutloop = False
        if self.port == 0:
            self.port = 6667
        self.connecttime = 0
        self.connectlock = thread.allocate_lock()
        self.encoding = 'utf-8'
        self.blocking = 1
        self.lastoutput = 0
        if self.cfg and self.cfg.ipv6:
            self.ipv6 = 1
        else:
            self.ipv6 = 0

    def __del__(self):
        self.exit()

    def _raw(self, txt):
 
        """ send raw text to the server. """

        if not txt or self.stopped or not self.sock:
            logging.warn("irc - bot is stopped .. not sending.")
            return 0

        logging.debug("irc - sending %s" % txt)

        try:
            self.lastoutput = time.time()
            itxt = fromenc(outputmorphs.do(txt), self.encoding)
            if self.cfg.has_key('ssl') and self.cfg['ssl']:
                self.sock.write(itxt + '\n')
            else:
                self.sock.send(itxt[:500] + '\n')
        except UnicodeEncodeError, ex:
            logging.error("irc - encoding error: %s" % str(ex))
            return
        except Exception, ex:
            # check for broken pipe error .. if so ignore 
            # used for nonblocking sockets
            handle_exception()
            try:
                try:
                    (errno, errstr) = ex
                except ValueError:
                    errno = 0
                    errstr = str(ex)
                if errno != 32 and errno != 9:
                    raise
                else:
                    time.sleep(0.5)
            except:
                pass
            logging.warn("irc - ERROR: can't send %s" % str(ex))

    def _connect(self):

        """ connect to server/port using nick. """

        if self.connecting:
            raise AlreadyConnecting()

        if self.connected:
            raise AlreadyConnected()

        self.stopped = 0
        self.connecting = True
        self.connectok.clear()

        # create socket
        if self.cfg.ipv6 or self.ipv6:
            self.oldsock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self.ipv6 = 1
        else:
            self.oldsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        assert(self.oldsock)

        # optional bind
        server = self.server
        elite = self.cfg['bindhost'] or config['bindhost']
        if elite:
            try:
                self.oldsock.bind((elite, 0))
            except socket.gaierror:
                logging.warn("irc - %s - can't bind to %s" % (self.name, elite))
                # resolve the IRC server and pick a random server
                if not server:
                    # valid IPv6 ip?
                    try: socket.inet_pton(socket.AF_INET6, self.server)
                    except socket.error: pass
                    else: server = self.server
                if not server:  
                    # valid IPv4 ip?
                    try: socket.inet_pton(socket.AF_INET, self.server)
                    except socket.error: pass
                    else: server = self.server
                if not server:
                    # valid hostname?
                    ips = []
                    try:
                        for item in socket.getaddrinfo(self.server, None):
                            if item[0] in [socket.AF_INET, socket.AF_INET6] and item[1] == socket.SOCK_STREAM:
                                ip = item[4][0]
                                if ip not in ips: ips.append(ip)
                    except socket.error: pass
                    else: server = random.choice(ips)

        # do the connect .. set timeout to 30 sec upon connecting
        logging.warn('irc - connecting to %s (%s)' % (server, self.server))
        self.oldsock.settimeout(15)
        self.oldsock.connect((server, int(self.port)))

        # we are connected
        logging.warn('irc - connection ok')
        self.connected = True

        # make file socket
        self.fsock = self.oldsock.makefile("r")

        # set blocking
        self.oldsock.setblocking(self.blocking)
        self.fsock._sock.setblocking(self.blocking)

        # set socket time out
        if self.blocking:
            socktimeout = self.cfg['socktimeout']
            if not socktimeout:
                socktimeout = 301.0
            else:
                socktimeout = float(socktimeout)
            self.oldsock.settimeout(socktimeout)
            self.fsock._sock.settimeout(socktimeout)
        # enable ssl if set
        if self.cfg.has_key('ssl') and self.cfg['ssl']:
            logging.info('irc - ssl enabled')
            self.sock = socket.ssl(self.oldsock) 
        else:
            self.sock = self.oldsock

        # try to release the outputlock
        try:
            self.outputlock.release()
        except thread.error:
            pass
        self.connecttime = time.time()
        return 1

    def start(self):
        """ start the bot. """
        if self.stopped:
            logging.warn("irc - bot is stopped .. not starting.")
            return 0

        logging.warn("irc - starting")
        self._connect()
        # start input and output loops
        logging.info("irc - starting loops")
        start_new_thread(self._readloop, ())
        start_new_thread(self._outloop, ())

        # logon and start monitor
        logging.info("irc - logon")
        self._logon()
        self.nickchanged = 0
        self.reconnectcount = 0
        self.connectok.wait()
        logging.warn("irc - logged on!")
        return True

    def _readloop(self):

        """ loop on the socketfile. """

        self.stopreadloop = 0
        self.stopped = 0
        doreconnect = 1
        timeout = 1
        logging.info('irc - starting readloop')
        prevtxt = ""

        while not self.stopped and not self.stopreadloop:

            try:
                time.sleep(0.01)
                if self.cfg.has_key('ssl') and self.cfg['ssl']:
                    intxt = inputmorphs.do(self.sock.read()).split('\n')
                else:
                    intxt = inputmorphs.do(self.fsock.readline()).split('\n')
                # if intxt == "" the other side has disconnected
                if self.stopreadloop or self.stopped:
                    doreconnect = 0
                    break
                if not intxt or not intxt[0]:
                    doreconnect = 1
                    break
                if prevtxt:
                    intxt[0] = prevtxt + intxt[0]
                    prevtxt = ""
                if intxt[-1] != '':
                    prevtxt = intxt[-1]
                    intxt = intxt[:-1]
                for r in intxt:
                    r = r.rstrip()
                    try:
                        rr = unicode(fromenc(r, self.encoding))
                    except UnicodeDecodeError:
                        logging.warn("irc - decode error - ignoring")
                        continue
                        #rr = toenc(r, self.encoding)
                    if not rr:
                        continue
                    res = strippedtxt(rr, ['\001', '\002', '\003', '\t'])
                    res = rr
                    logging.debug(u"irc - %s" % res)
                    # parse txt read into an ircevent
                    try:
                        ievent = Ircevent().parse(self, res)
                    except Exception, ex:
                        handle_exception()
                        continue
                    # call handle_ievent 
                    if ievent:
                        self.handle_ievent(ievent)
                    timeout = 1

            except UnicodeError:
                handle_exception()
                continue

            except socket.timeout:
                # timeout occured .. first time send ping .. reconnect if
                # second timeout follows
                if self.stopped:
                    break
                timeout += 1
                if timeout > 2:
                    doreconnect = 1
                    logging.warn('irc - no pong received')
                    break
                logging.debug("irc - socket timeout")
                pingsend = self.ping()
                if not pingsend:
                    doreconnect = 1
                    break
                continue

            except socket.sslerror, ex:
                # timeout occured .. first time send ping .. reconnect if
                # second timeout follows
                if self.stopped or self.stopreadloop:
                    break
                if not 'timed out' in str(ex):
                    handle_exception()
                    doreconnect = 1
                    break
                timeout += 1
                if timeout > 2:
                    doreconnect = 1
                    logging.warn('irc - no pong received')
                    break
                logging.error("irc - socket timeout")
                pingsend = self.ping()
                if not pingsend:
                    doreconnect = 1
                    break
                continue
            except IOError, ex:
                if self.blocking and 'temporarily' in str(ex):
                    time.sleep(0.5)
                    continue
                logging.error('connecting error: %s' % str(ex))
                doreconnect = 1
                break
                #handle_exception()
                #doreconnect = 1
                #break
            except socket.error, ex:
                if self.blocking and 'temporarily' in str(ex):
                    time.sleep(0.5)
                    continue
                logging.error('connecting error: %s' % str(ex))
                doreconnect = 1
                break
                #handle_exception()
                #doreconnect = 1
                #break
            except Exception, ex:
                if self.stopped or self.stopreadloop:
                    break
                err = ex
                try:
                    (errno, msg) = ex
                except:
                    errno = -1
                    msg = err
                # check for temp. unavailable error .. raised when using
                # nonblocking socket .. 35 is FreeBSD 11 is Linux
                if errno == 35 or errno == 11:
                    time.sleep(0.5)
                    continue
                logging.error("irc - error in readloop: %s" % msg)
                doreconnect = 1
                break

        logging.info('irc - readloop stopped')
        self.connectok.clear()
        self.connected = False

        # see if we need to reconnect
        if doreconnect and not self.stopped:
            time.sleep(2)
            self.reconnect()

    def _getqueue(self):

        """ get one of the outqueues. """

        go = self.tickqueue.get()
        for index in range(len(self.outqueues)):
            if not self.outqueues[index].empty():
                return self.outqueues[index]

    def putonqueue(self, nr, *args):

        """ put output onto one of the output queues. """

        self.outqueues[nr].put_nowait(*args)
        self.tickqueue.put_nowait('go')

    def _outloop(self):

        """ output loop. """

        logging.debug('irc - starting output loop')
        self.stopoutloop = 0

        while not self.stopped and not self.stopoutloop:
            queue = self._getqueue()
            if queue:
                try:
                    res = queue.get()
                except Queue.Empty:
                    continue
                if not res:
                    continue
                try:
                    (printto, what, who, how, fromm, speed) = res
                except ValueError:
                    self.send(res)
                    continue
                if not self.stopped and not self.stopoutloop and printto not in self.nicks401:
                    self.out(printto, what, who, how, fromm, speed)
            else:
                time.sleep(0.1)

        logging.debug('irc - stopping output loop')

    def _logon(self):

        """ log on to the network. """

        # if password is provided send it
        if self.password:
            logging.debug('irc - sending password')
            self._raw("PASS %s" % self.password)

        # register with irc server
        logging.debug('irc - registering with %s using nick %s' % (self.server, self.nick))
        logging.debug('irc - this may take a while')

        # check for username and realname
        username = self.nick or 'jsonbot'
        realname = self.cfg['realname'] or username

        # first send nick
        time.sleep(1)
        self._raw("NICK %s" % self.nick)
        time.sleep(1)

        # send USER
        self._raw("USER %s localhost localhost :%s" % (username, \
realname))

        # wait on login
        self.connectok.wait()

    def _onconnect(self):

        """ overload this to run after connect. """

        pass

    def say(self, printto, what, event=None, how='msg', origin="", extend=0):
        self.out(printto, what, how)
        self.outmonitor(origin or self.nick, printto, what, event)

    def saynocb(self, printto, what, event=None, how='msg', origin="", extend=0):
        self.out(printto, what, how)

    def out(self, printto, what, how):
        # check for socket
        # normal
        what = self.normalize(what)

        if 'socket' in repr(printto): 
            try:
                printto.send(what + '\n')
                time.sleep(0.001)
            except Exception, ex :
                if "Broken pipe" in str(ex) or "Bad file descriptor" in str(ex):
                    return
                raise
            return

        if how == 'notice':
            self.notice(printto, what)
        elif how == 'ctcp':
            self.ctcp(printto, what)
        else:
            self.privmsg(printto, what)

    def _resume(self, data, reto=None):

        """ resume to server/port using nick. """

        try:
            if data['ssl']:
                self.connectwithjoin()
                return 1
        except KeyError:
            pass

        try:
            logging.warn("irc - resume - file descriptor is %s" % data['fd'])
            fd = int(data['fd'])
        except (TypeError, ValueError):
            fd = None
            logging.error("irc - can't determine file descriptor")
            return 0
 
        self.connecting = False # we're already connected
        self.nick = data['nick']
        self.orignick = self.nick
        self.server = str(data['server'])
        self.port = int(data['port'])
        self.password = data['password']
        self.ipv6 = data['ipv6']
        self.ssl = data['ssl']

        # create socket
        if self.ipv6:
            if fd:
                self.sock = socket.fromfd(fd , socket.AF_INET6, socket.SOCK_STREAM)
            else:
                self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self.ipv6 = 1
        else:
            if fd:
                self.sock = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
            else:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # do the connect .. set timeout to 30 sec upon connecting
        logging.info('irc - resuming to ' + self.server)
        self.sock.settimeout(30)
        self.stopped = 0
        # make file socket
        self.fsock = self.sock.makefile("r")
        # set blocking
        self.sock.setblocking(self.blocking)

        # set socket time out
        if self.blocking:
            socktimeout = self.cfg['socktimeout']
            if not socktimeout:
                socktimeout = 301.0
            else:
                socktimeout = float(socktimeout)
            self.sock.settimeout(socktimeout)

        # start readloop
        logging.debug('resuming readloop')
        start_new_thread(self._readloop, ())
        start_new_thread(self._outloop, ())

        # init 
        self.reconnectcount = 0
        self.nickchanged = 0
        self.connecting = False

        # still there server?
        self._raw('PING :RESUME %s' % str(time.time()))
        self.connectok.set()
        self.connected = True
        self.reconnectcount = 0
        if reto:
            self.say(reto, 'rebooting done')
        return 1

    def _resumedata(self):

        """ return data used for resume. """
        try:
            fd = self.sock.fileno()
        except AttributeError, ex:
            logging.error("can't detect fileno of socket")
            fd = None
            self.exit()
        return {self.name: {
            'type': self.type,
            'nick': self.nick,
            'server': self.server,
            'port': self.port,
            'password': self.password,
            'ipv6': self.ipv6,
            'ssl': self.ssl,
            'fd': fd
            }}


    def outputsizes(self):

        """ return sizes of output queues. """

        result = []
        for q in self.outqueues:
            result.append(q.qsize())
        return result

    def broadcast(self, txt):

        """ broadcast txt to all joined channels. """

        for i in self.state['joinedchannels']:
            self.say(i, txt, speed=-1)

    def normalize(self, what):
        txt = re.sub("\s+", " ", what)
        txt = txt.replace("<b>", "\002")
        txt = txt.replace("</b>", "\002")
        txt = txt.replace("&lt;b&gt;", "\002")
        txt = txt.replace("&lt;/b&gt;", "\002")
        txt = txt.replace("&lt;h2&gt;", "\002")
        txt = txt.replace("&lt;/h2&gt;", "\002")
        txt = txt.replace("&lt;h3&gt;", "\002")
        txt = txt.replace("&lt;/h3&gt;", "\002")
        txt = txt.replace("&lt;li&gt;", "\002")
        txt = txt.replace("&lt;/li&gt;", "\002")
        return txt

    def save(self):

        """ save state data. """

        if self.state:
            self.state.save()

    def connect(self, reconnect=True):

        """ connect to server/port using nick .. connect can timeout so catch
            exception .. reconnect if enabled.
        """

        res = 0

        try:
            res = self.start()
            if res:
                logging.warn("waiting for connectok")
                self.connectok.wait()
                self._onconnect()
                self.connected = True
                logging.warn('logged on !')
            self.connecting = False
        except (socket.gaierror, socket.error), ex:
            #if "Connection timed out" in str(ex):
            logging.error('connecting error: %s' % str(ex))
            self.reconnect()
            return
        except AlreadyConnecting:
            return 0 
        except AlreadyConnected:
            return 0
        except Exception, ex:
            if self.stopped:
                return 0
            logging.error('connecting error: %s' % str(ex))
            if reconnect:
                self.reconnect()
                return
            raise

        return res

    def shutdown(self):

        """ shutdown the bot. """

        logging.warn('irc - shutdown')
        self.stopoutputloop = 1
        #self.stopped = 1
        time.sleep(1)
        self.tickqueue.put_nowait('go')
        self.close()
        self.connecting = False
        self.connected = False
        self.connectok.clear()

    def close(self):

        """ close the connection. """

        try:
            if self.cfg.has_key('ssl') and self.cfg['ssl']:
                self.oldsock.shutdown(2)
            else:
                self.sock.shutdown(2)
        except:
            pass
        try:
            if self.cfg.has_key('ssl') and self.cfg['ssl']:
                self.oldsock.close()
            else:
                self.sock.close()
            self.fsock.close()
        except:
            pass

    def exit(self):

        """ exit the bot. """
        self.stopped = True
        self.stopreadloop = True
        self.connected = False
        self.quit()
        time.sleep(1)
        self.shutdown()

    def handle_pong(self, ievent):

        """ set pongcheck on received pong. """

        logging.debug('received server pong')
        self.pongcheck = 1

    def sendraw(self, txt):

        """ send raw text to the server. """

        if self.stopped:
            return
        logging.debug(u'irc - sending %s' % txt)
        self._raw(txt)

    def fakein(self, txt):

        """ do a fake ircevent. """

        if not txt:
            return
        logging.warn('irc - fakein - %s' % txt)
        self.handle_ievent(Ircevent().parse(self, txt))

    def donick(self, nick, setorig=0, save=0, whois=0):

        """ change nick .. optionally set original nick and/or save to config.  """

        if not nick:
            return

        # disable auto 433 nick changing
        self.noauto433 = 1

        # set up wait for NICK command and issue NICK
        queue = Queue.Queue()
        nick = nick[:16]
        self.wait.register('NICK', self.nick[:16], queue, 12)
        self._raw('NICK %s\n' % nick)
        result = waitforqueue(queue, 5)

        # reenable 433 auto nick changing
        self.noauto433 = 0
        if not result:
            return 0
        self.nick = nick

        # send whois
        if whois:
            self.whois(nick)

        # set original
        if setorig:
            self.orignick = nick
            self.cfg.orignick = nick
            
        # save nick to state and config file
        if save:
            self.state['nick'] = nick
            self.state.save()
            self.cfg.set('nick', nick)
            self.cfg.save()
        return 1

    def join(self, channel, password=None):

        """ join channel with optional password. """

        if not channel:
            return

        # do join with password
        if password:
            self._raw('JOIN %s %s' % (channel, password))
            chan = ChannelBase(channel)
            if chan:
                chan.setpass('IRC', password)            
        else:
            # do pure join
            self._raw('JOIN %s' % channel)

        if self.state:
            if channel not in self.state.data.joinedchannels:
                self.state.data.joinedchannels.append(channel)
                self.state.save()

    def part(self, channel):

        """ leave channel. """

        if not channel:
            return
        self._raw('PART %s' % channel)

        try:
            self.state.data['joinedchannels'].remove(channel)
            self.state.save()
        except (KeyError, ValueError):
            pass

    def who(self, who):

        """ send who query. """

        if not who:
            return
        self.putonqueue(4, 'WHO %s' % who.strip())

    def names(self, channel):

        """ send names query. """

        if not channel:
            return
        self.putonqueue(4, 'NAMES %s' % channel)

    def whois(self, who):

        """ send whois query. """

        if not who:
            return
        self.putonqueue(4, 'WHOIS %s' % who)

    def privmsg(self, printto, what):

        """ send privmsg to irc server. """

        if not printto or not what:
            return
        self.send('PRIVMSG %s :%s' % (printto, what))

    def send(self, txt):

        """ send text to irc server. """

        if not txt:
            return

        if self.stopped:
            return

        try:
            self.outputlock.acquire()
            now = time.time()
            timetosleep = 4 - (now - self.lastoutput)
            if timetosleep > 0 and not self.nolimiter and not (time.time() - self.connecttime < 5):
                logging.debug('irc - flood protect')
                time.sleep(timetosleep)
            txt = strippedtxt(txt, ['\001', '\002', '\003', '\t'])
            txt = txt.rstrip()
            self._raw(txt)
            try:
                self.outputlock.release()
            except:
                pass
        except Exception, ex:
            try:
                self.outputlock.release()
            except:
                pass
            if not self.blocking and 'broken pipe' in str(ex).lower():
                time.sleep(0.5)
            else:
                logging.error('irc - send error: %s' % str(ex))
                handle_exception()
                self.reconnect()
                return
            
    def voice(self, channel, who):

        """ give voice. """

        if not channel or not who:
            return
        self.putonqueue(9, 'MODE %s +v %s' % (channel, who))
 
    def doop(self, channel, who):

        """ give ops. """

        if not channel or not who:
            return
        self._raw('MODE %s +o %s' % (channel, who))

    def delop(self, channel, who):

        """ de-op user. """

        if not channel or not who:
            return
        self._raw('MODE %s -o %s' % (channel, who))

    def quit(self, reason='http://jsonbot.googlecode.com'):

        """ send quit message. """

        logging.debug('irc - sending quit')
        try:
            self._raw('QUIT :%s' % reason)
            time.sleep(1)
        except IOError:
            pass

    def notice(self, printto, what):

        """ send notice. """

        if not printto or not what:
            return
        self.send('NOTICE %s :%s' % (printto, what))
 
    def ctcp(self, printto, what):

        """ send ctcp privmsg. """

        if not printto or not what:
            return
        self.send("PRIVMSG %s :\001%s\001" % (printto, what))

    def ctcpreply(self, printto, what):

        """ send ctcp notice. """

        if not printto or not what:
            return
        self.putonqueue(2, "NOTICE %s :\001%s\001" % (printto, what))

    def action(self, printto, what):

        """ do action. """

        if not printto or not what:
            return
        self.putonqueue(9, "PRIVMSG %s :\001ACTION %s\001" % (printto, what))

    def handle_ievent(self, ievent):

        """ handle ircevent .. dispatch to 'handle_command' method. """ 

        try:
            if ievent.cmnd == 'JOIN' or ievent.msg:
                if ievent.nick in self.nicks401:
                    self.nicks401.remove(ievent.nick)
                    logging.debug('irc - %s joined .. unignoring' % ievent.nick)
            # see if the irc object has a method to handle the ievent
            method = getattr(self,'handle_' + ievent.cmnd.lower())
            # try to call method
            if method:
                try:
                    method(ievent)
                except:
                    handle_exception()
        except AttributeError:
            # no command method to handle event
            pass
        try:
            # see if there are wait callbacks
            self.wait.check(ievent)
        except:
            handle_exception()

    def handle_432(self, ievent):

        """ erroneous nick. """

        self.handle_433(ievent)

    def handle_433(self, ievent):

        """ handle nick already taken. """

        if self.noauto433:
            return
        nick = ievent.arguments[1]
        # check for alternick
        alternick = self.state['alternick']
        if alternick and not self.nickchanged:
            logging.debug('irc - using alternick %s' % alternick)
            self.donick(alternick)
            self.nickchanged = 1
            return
        # use random nick
        randomnick = getrandomnick()
        self._raw("NICK %s" % randomnick)
        self.nick = randomnick
        logging.warn('irc - ALERT: nick %s already in use/unavailable .. using randomnick %s' % (nick, randomnick))
        self.nickchanged = 1

    def handle_ping(self, ievent):

        """ send pong response. """

        if not ievent.txt:
            return
        self._raw('PONG :%s' % ievent.txt)

    def handle_001(self, ievent):

        """ we are connected.  """

        self.connectok.set()
        self.connected = True
        self.whois(self.nick)

    def handle_privmsg(self, ievent):

        """ check if msg is ctcp or not .. return 1 on handling. """

        if ievent.txt and ievent.txt[0] == '\001':
            self.handle_ctcp(ievent)
            return 1

    def handle_notice(self, ievent):

        """ handle notice event .. check for version request. """

        if ievent.txt and ievent.txt.find('VERSION') != -1:
            self.say(ievent.nick, self.cfg['version'], None, 'notice')
            return 1

    def handle_ctcp(self, ievent):

        """ handle client to client request .. version and ping. """

        if ievent.txt.find('VERSION') != -1:
            self.ctcpreply(ievent.nick, 'VERSION %s' % self.cfg['version'])

        if ievent.txt.find('PING') != -1:
            try:
                pingtime = ievent.txt.split()[1]
                pingtime2 = ievent.txt.split()[2]
                if pingtime:
                    self.ctcpreply(ievent.nick, 'PING ' + pingtime + ' ' + \
pingtime2)
            except IndexError:
                pass

    def handle_error(self, ievent):

        """ show error. """
        if ievent.cmnd == "422":
            return

        if ievent.txt.startswith('Closing'):
            logging.error("irc - %s" % ievent.txt)
        else:
            logging.error("irc - %s - %s" % (ievent.arguments, ievent.txt))

    def ping(self):

        """ ping the irc server. """

        logging.debug('irc - sending ping')
        try:
            self._raw('PING :%s' % self.server)
            return 1
        except Exception, ex:
            logging.debug("irc - can't send ping: %s" % str(ex))
            return 0

    def handle_401(self, ievent):

        """ handle 401 .. nick not available. """

        try:
            nick = ievent.arguments[1]
            #if nick not in self.nicks401:
            #    logging.warn('irc - 401 on %s .. ignoring' % nick)
            #    self.nicks401.append(nick)
        except:
            pass

    def handle_700(self, ievent):

        """ handle 700 .. encoding request of the server. """

        try:
            self.encoding = ievent.arguments[1]
            logging.warn('irc - 700 encoding now is %s' % self.encoding)
        except:
            pass
