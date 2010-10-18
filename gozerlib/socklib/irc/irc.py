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

from ircevent import IrcEvent
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

class Irc(BotBase):

    """ the irc class, provides interface to irc related stuff. """

    def __init__(self, cfg=None, users=None, plugs=None, *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, *args, **kwargs)
        BotBase.setstate(self)
        self.type = 'irc'
        self.wait = Wait()
        self.fsock = None
        self.oldsock = None
        self.sock = None
        if self.cfg:
            if not self.cfg.nolimiter:
                self.nolimiter = False
        else: self.nolimiter = self.cfg.nolimiter
        self.reconnectcount = 0
        self.pongcheck = False
        self.nickchanged = False
        self.noauto433 = False
        if self.state:
            if not self.state.has_key('alternick'): self.state['alternick'] = self.cfg['alternick']
            if not self.state.has_key('no-op'): self.state['no-op'] = []
        self.nicks401 = []
        if self.port == 0: self.port = 6667
        self.connecttime = 0
        self.encoding = 'utf-8'
        self.blocking = 1
        self.lastoutput = 0
        if self.cfg and self.cfg.ipv6: self.ipv6 = True
        else: self.ipv6 = False

    def _raw(self, txt):
        """ send raw text to the server. """
        if not txt or self.stopped or not self.sock:
            logging.warn("%s - bot is stopped .. not sending." % self.name)
            return 0
        if not txt.startswith("PONG"): logging.warn("%s - sending %s" % (self.name, txt))
        try:
            self.lastoutput = time.time()
            itxt = toenc(outputmorphs.do(txt), self.encoding)
            #logging.debug(u"%s - out - %s" % (self.name, itxt))             
            if self.cfg.has_key('ssl') and self.cfg['ssl']: self.sock.write(itxt + '\n')
            else: self.sock.send(itxt[:500] + '\n')
        except UnicodeEncodeError, ex:
            logging.error("%s - encoding error: %s" % (self.name, str(ex)))
            return
        except Exception, ex:
            handle_exception()
            logging.warn("%s - ERROR: can't send %s" % (self.name, str(ex)))

    def _connect(self):
        """ connect to server/port using nick. """
        self.stopped = False
        self.connecting = True
        self.connectok.clear()
        if self.cfg.ipv6 or self.ipv6:
            self.oldsock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self.ipv6 = 1
        else:
            self.oldsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert(self.oldsock)
        server = self.bind()
        logging.warn('%s - connecting to %s (%s)' % (self.name, server, self.server))
        self.oldsock.settimeout(5)
        self.oldsock.connect((server, int(str(self.port))))	
        self.blocking = 1
        self.oldsock.setblocking(self.blocking)
        logging.warn('%s - connection ok' % self.name)
        self.connected = True
        self.fsock = self.oldsock.makefile("r")
        self.fsock._sock.setblocking(self.blocking)
        if self.blocking:
            socktimeout = self.cfg['socktimeout']
            if not socktimeout:
                socktimeout = 500.0
            else:
                socktimeout = float(socktimeout)
            self.oldsock.settimeout(socktimeout)
            self.fsock._sock.settimeout(socktimeout)
        if self.cfg.has_key('ssl') and self.cfg['ssl']:
            logging.info('%s - ssl enabled' % self.name)
            self.sock = socket.ssl(self.oldsock) 
        else: self.sock = self.oldsock
        try:
            self.outputlock.release()
        except thread.error:
            pass
        self.connecttime = time.time()
        return True

    def bind(self):
        server = self.server
        elite = self.cfg['bindhost'] or config['bindhost']
        if elite:
            try:
                self.oldsock.bind((elite, 0))
            except socket.gaierror:
                logging.warn("%s - can't bind to %s" % (self.name, elite))
                if not server:
                    try: socket.inet_pton(socket.AF_INET6, self.server)
                    except socket.error: pass
                    else: server = self.server
                if not server:  
                    try: socket.inet_pton(socket.AF_INET, self.server)
                    except socket.error: pass
                    else: server = self.server
                if not server:
                    ips = []
                    try:
                        for item in socket.getaddrinfo(self.server, None):
                            if item[0] in [socket.AF_INET, socket.AF_INET6] and item[1] == socket.SOCK_STREAM:
                                ip = item[4][0]
                                if ip not in ips: ips.append(ip)
                    except socket.error: pass
                    else: server = random.choice(ips)
        return server

    def _readloop(self):
        """ loop on the socketfile. """
        self.stopreadloop = False
        self.stopped = False
        doreconnect = True
        timeout = 1
        logging.info('%s - starting readloop' % self.name)
        prevtxt = ""
        while not self.stopped and not self.stopreadloop and self.sock and self.fsock:
            try:
                time.sleep(0.01)
                if self.cfg.has_key('ssl') and self.cfg['ssl']: intxt = inputmorphs.do(self.sock.read()).split('\n')
                else: intxt = inputmorphs.do(self.fsock.readline()).split('\n')
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
                    try:
                        r = strippedtxt(r.rstrip(), ["\001", "\002"]) 
                        rr = unicode(fromenc(r.rstrip(), self.encoding))
                    except UnicodeDecodeError:
                        logging.warn("%s - decode error - ignoring" % self.name)
                        continue
                    if not rr: continue
                    res = rr
                    logging.debug(u"%s - %s" % (self.name, res))
                    try:
                        ievent = IrcEvent().parse(self, res)
                    except Exception, ex:
                        handle_exception()
                        continue
                    if ievent:
                        self.handle_ievent(ievent)
                    timeout = 1
            except UnicodeError:
                handle_exception()
                continue
            except socket.timeout:
                if self.stopped or self.stopreadloop: break
                timeout += 1
                if timeout > 2:
                    doreconnect = 1
                    logging.warn('%s - no pong received' % self.name)
                    break
                logging.debug("%s - socket timeout" % self.name)
                pingsend = self.ping()
                if not pingsend:
                    doreconnect = 1
                    break
                continue
            except socket.sslerror, ex:
                if self.stopped or self.stopreadloop: break
                if not 'timed out' in str(ex):
                    handle_exception()
                    doreconnect = 1
                    break
                timeout += 1
                if timeout > 2:
                    doreconnect = 1
                    logging.warn('%s - no pong received' % self.name)
                    break
                logging.error("%s - socket timeout" % self.name)
                pingsend = self.ping()
                if not pingsend:
                    doreconnect = 1
                    break
                continue
            except IOError, ex:
                if self.blocking and 'temporarily' in str(ex):
                    time.sleep(0.5)
                    continue
                if not self.stopped:
                    logging.error('%s - connecting error: %s' % (self.name, str(ex)))
                    handle_exception()
                    doreconnect = 1
                break
            except socket.error, ex:
                if self.blocking and 'temporarily' in str(ex):
                    time.sleep(0.5)
                    continue
                if not self.stopped:
                    logging.error('%s - connecting error: %s' % (self.name, str(ex)))
                    doreconnect = 1
            except Exception, ex:
                if self.stopped or self.stopreadloop:
                    break
                logging.error("%s - error in readloop: %s" % (self.name, msg))
                doreconnect = 1
                break
        logging.info('%s - readloop stopped' % self.name)
        self.connectok.clear()
        self.connected = False
        if doreconnect and not self.stopped:
            time.sleep(2)
            self.reconnect()

    def logon(self):
        """ log on to the network. """
        if self.password:
            logging.debug('%s - sending password' % self.name)
            self._raw("PASS %s" % self.password)
        logging.warn('%s - registering with %s using nick %s' % (self.name, self.server, self.nick))
        logging.warn('%s - this may take a while' % self.name)
        username = self.cfg['username'] or "jsonbot"
        realname = self.cfg['realname'] or "The JSON everywhere bot"
        time.sleep(1)
        self._raw("NICK %s" % self.nick)
        time.sleep(1)
        self._raw("USER %s localhost %s :%s" % (username, self.server, realname))

    def _onconnect(self):
        """ overload this to run after connect. """
        pass

    def _resume(self, data, reto=None):
        """ resume to server/port using nick. """
        try:
            if data['ssl']:
                self.start()
                return 1
        except KeyError:
            pass
        try:
            logging.info("%s - resume - file descriptor is %s" % (self.name, data['fd']))
            fd = int(data['fd'])
        except (TypeError, ValueError):
            fd = None
            logging.error("%s - can't determine file descriptor" % self.name)
            return 0
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
        self.sock.settimeout(30)
        self.fsock = self.sock.makefile("r")
        self.sock.setblocking(self.blocking)
        if self.blocking:
            socktimeout = self.cfg['socktimeout']
            if not socktimeout: socktimeout = 301.0
            else: socktimeout = float(socktimeout)
            self.sock.settimeout(socktimeout)
        self.nickchanged = 0
        self.connecting = False
        self._raw('PING :RESUME %s' % str(time.time()))
        self.dostart(self.name, self.type)
        self.connectok.set()
        self.connected = True
        self.reconnectcount = 0
        if reto: self.say(reto, 'rebooting done')
        logging.warn("%s - rebooting done" % self.name)
        return True

    def _resumedata(self):
        """ return data used for resume. """
        try:
            fd = self.sock.fileno()
        except AttributeError, ex:
            logging.error("%s - can't detect fileno of socket" % self.name)
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

    def outnocb(self, printto, what, how='msg', *args, **kwargs):
        if printto in self.nicks401:
             logging.warn("%s - blocking %s" % (self.name, printto))
             return
        if 'socket' in repr(printto) and self.sock:
            printto.send(unicode(what) + u"\n")
            return True
        what = fix_format(what)
        what = self.normalize(what)
        if not printto: self._raw(what)
        elif how == 'notice': self.notice(printto, what)
        elif how == 'ctcp': self.ctcp(printto, what)
        else: self.privmsg(printto, what)

    def broadcast(self, txt):
        """ broadcast txt to all joined channels. """
        for i in self.state['joinedchannels']:
            self.say(i, txt, speed=1)

    def normalize(self, what):
        txt = strippedtxt(what, ["\001", "\002"])
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

    def save(self):
        """ save state data. """
        if self.state: self.state.save()

    def connect(self):
        """ 
            connect to server/port using nick .. connect can timeout so catch
            exception .. reconnect if enabled.
        """
        try:
            self._connect()
            logging.info("%s - logon" % self.name)
            self.logon()
            time.sleep(1)
            self.nickchanged = 0
            self.reconnectcount = 0
            self._onconnect()
            self.connected = True
            logging.warn('%s - logged on !' % self.name)
            self.connecting = False
        except (socket.gaierror, socket.error), ex:
            logging.error('%s - connecting error: %s' % (self.name, str(ex)))
            return
        except Exception, ex:
            handle_exception()
            logging.error('%s - connecting error: %s' % (self.name, str(ex)))

    def shutdown(self):
        """ shutdown the bot. """
        logging.warn('%s - shutdown' % self.name)
        self.stopoutputloop = 1
        self.close()
        self.connecting = False
        self.connected = False
        self.connectok.clear()

    def close(self):
        """ close the connection. """
        try:
            if self.cfg.has_key('ssl') and self.cfg['ssl']: self.oldsock.shutdown(2)
            else: self.sock.shutdown(2)
        except:
            pass
        try:
            if self.cfg.has_key('ssl') and self.cfg['ssl']: self.oldsock.close()
            else: self.sock.close()
            self.fsock.close()
        except:
            pass

    def handle_pong(self, ievent):
        """ set pongcheck on received pong. """
        logging.debug('%s - received server pong' % self.name)
        self.pongcheck = 1

    def sendraw(self, txt):
        """ send raw text to the server. """
        if self.stopped: return
        logging.debug(u'%s - sending %s' % (self.name, txt))
        self._raw(txt)

    def fakein(self, txt):
        """ do a fake ircevent. """
        if not txt: return
        logging.debug('%s - fakein - %s' % (self.name, txt))
        self.handle_ievent(IrcEvent().parse(self, txt))

    def donick(self, nick, setorig=False, save=False, whois=False):
        """ change nick .. optionally set original nick and/or save to config.  """
        if not nick: return
        self.noauto433 = True
        nick = nick[:16]
        self._raw('NICK %s\n' % nick)
        self.noauto433 = False

    def join(self, channel, password=None):
        """ join channel with optional password. """
        if not channel: return
        if password:
            self._raw('JOIN %s %s' % (channel, password))
            chan = ChannelBase(channel)
            if chan: chan.setpass('IRC', password)            
        else: self._raw('JOIN %s' % channel)
        if self.state:
            if channel not in self.state.data.joinedchannels:
                self.state.data.joinedchannels.append(channel)
                self.state.save()

    def part(self, channel):
        """ leave channel. """
        if not channel: return
        self._raw('PART %s' % channel)
        try:
            self.state.data['joinedchannels'].remove(channel)
            self.state.save()
        except (KeyError, ValueError):
            pass

    def who(self, who):
        """ send who query. """
        if not who: return
        self.putonqueue(4, None, 'WHO %s' % who.strip())

    def names(self, channel):
        """ send names query. """
        if not channel: return
        self.putonqueue(4, None, 'NAMES %s' % channel)

    def whois(self, who):
        """ send whois query. """
        if not who: return
        self.putonqueue(4, None, 'WHOIS %s' % who)

    def privmsg(self, printto, what):
        """ send privmsg to irc server. """
        if not printto or not what: return
        self.send('PRIVMSG %s :%s' % (printto, what))

    @outlocked
    def send(self, txt):
        """ send text to irc server. """
        if not txt: return
        if self.stopped: return
        try:
            now = time.time()
            timetosleep = 4 - (now - self.lastoutput)
            if timetosleep > 0 and not self.nolimiter and not (time.time() - self.connecttime < 5):
                logging.debug('%s - flood protect' % self.name)
                time.sleep(timetosleep)
            txt = txt.rstrip()
            self._raw(txt)
        except Exception, ex:
            logging.error('%s - send error: %s' % (self.name, str(ex)))
            handle_exception()
            return
            
    def voice(self, channel, who):
        """ give voice. """
        if not channel or not who: return
        self.putonqueue(9, None, 'MODE %s +v %s' % (channel, who))
 
    def doop(self, channel, who):
        """ give ops. """
        if not channel or not who: return
        self._raw('MODE %s +o %s' % (channel, who))

    def delop(self, channel, who):
        """ de-op user. """
        if not channel or not who: return
        self._raw('MODE %s -o %s' % (channel, who))

    def quit(self, reason='http://jsonbot.googlecode.com'):
        """ send quit message. """
        logging.warn('%s - sending quit - %s' % (self.name, reason))
        self._raw('QUIT :%s' % reason)

    def notice(self, printto, what):
        """ send notice. """
        if not printto or not what: return
        self.putonqueue(3, None, 'NOTICE %s :%s' % (printto, what))
 
    def ctcp(self, printto, what):
        """ send ctcp privmsg. """
        if not printto or not what: return
        self.putonqueue(3, None, "PRIVMSG %s :\001%s\001" % (printto, what))

    def ctcpreply(self, printto, what):
        """ send ctcp notice. """
        if not printto or not what: return
        self.putonqueue(3, None, "NOTICE %s :\001%s\001" % (printto, what))

    def action(self, printto, what):
        """ do action. """
        if not printto or not what: return
        self.putonqueue(9, None, "PRIVMSG %s :\001ACTION %s\001" % (printto, what))

    def handle_ievent(self, ievent):
        """ handle ircevent .. dispatch to 'handle_command' method. """ 
        try:
            if ievent.cmnd == 'JOIN' or ievent.msg:
                if ievent.nick in self.nicks401:
                    self.nicks401.remove(ievent.nick)
                    logging.debug('%s - %s joined .. unignoring' % (self.name, ievent.nick))
            #if not ievent.chan and ievent.channel:
            #    ievent.chan = ChannelBase(ievent.channel)
            method = getattr(self,'handle_' + ievent.cmnd.lower())
            if method:
                try:
                    method(ievent)
                except:
                    handle_exception()
        except AttributeError:
            pass
        try:
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
        alternick = self.state['alternick']
        if alternick and not self.nickchanged:
            logging.debug('%s - using alternick %s' % (self.name, alternick))
            self.donick(alternick)
            self.nickchanged = 1
            return
        randomnick = getrandomnick()
        self._raw("NICK %s" % randomnick)
        self.nick = randomnick
        logging.warn('%s - ALERT: nick %s already in use/unavailable .. using randomnick %s' % (self.name, nick, randomnick))
        self.nickchanged = 1

    def handle_ping(self, ievent):
        """ send pong response. """
        if not ievent.txt: return
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
            self.ctcpreply(ievent.nick, 'VERSION %s' % config.version)
        if ievent.txt.find('PING') != -1:
            try:
                pingtime = ievent.txt.split()[1]
                pingtime2 = ievent.txt.split()[2]
                if pingtime:
                    self.ctcpreply(ievent.nick, 'PING ' + pingtime + ' ' + pingtime2)
            except IndexError:
                pass

    def handle_error(self, ievent):
        """ show error. """
        txt = ievent.txt
        if txt.startswith('Closing'):
            if "banned" in txt.lower(): logging.error("WE ARE BANNED !! - %s - %s" % (self.server, ievent.txt)) ; self.exit()
            else: logging.error("%s - %s" % (self.name, txt))
        else: logging.error("%s - %s - %s" % (self.name.upper(), ", ".join(ievent.arguments[1:]), txt))

    def ping(self):
        """ ping the irc server. """
        logging.debug('%s - sending ping' % self.name)
        try:
            self._raw('PING :%s' % self.server)
            return 1
        except Exception, ex:
            logging.debug("%s - can't send ping: %s" % (self.name, str(ex)))
            return 0

    def handle_401(self, ievent):
        """ handle 401 .. nick not available. """
        pass

    def handle_700(self, ievent):
        """ handle 700 .. encoding request of the server. """
        try:
            self.encoding = ievent.arguments[1]
            logging.warn('%s - 700 encoding now is %s' % (self.name, self.encoding))
        except:
            pass

    def handle_465(self, ievent):
        """ we are banned.. exit the bot. """
        self.exit()
