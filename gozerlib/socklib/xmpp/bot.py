# gozerlib/socklib/xmpp/bot.py
#
#

""" jabber bot definition """

## gozerlib imports

from gozerlib.users import users
from gozerlib.utils.exception import handle_exception
from gozerlib.utils.trace import whichmodule
from gozerlib.utils.locking import lockdec
from gozerlib.utils.pdod import Pdod
from gozerlib.utils.dol import Dol
from gozerlib.datadir import datadir
from gozerlib.less import Less
from gozerlib.callbacks import callbacks, gn_callbacks
from gozerlib.threads import start_new_thread
from gozerlib.fleet import fleet
from gozerlib.botbase import BotBase
from gozerlib.exit import globalshutdown

## gozerlib.socket imports

from gozerlib.socklib.utils.generic import waitforqueue, toenc, fromenc, jabberstrip, getrandomnick

## xmpp imports

from presence import Presence
from message import Message
from iq import Iq
from core import XMLStream
from wait import XMPPWait, XMPPErrorWait
from jid import JID, InvalidJID
from errors import xmpperrors
## basic imports

import time
import Queue
import os
import threading
import thread
import types
import xml
import re
import hashlib
import logging

## locks

outlock = thread.allocate_lock()
inlock = thread.allocate_lock()
connectlock = thread.allocate_lock()
outlocked = lockdec(outlock)
inlocked = lockdec(inlock)
connectlocked = lockdec(connectlock)

## classes

class SXMPPBot(XMLStream, BotBase):

    """
        xmpp bot class.

    """

    def __init__(self, cfg=None, usersin=None, plugs=None, jid=None, *args, **kwargs):
        BotBase.__init__(self, cfg, usersin, plugs, jid, *args, **kwargs)
        self.port = 5222
        if not self.host:
            self.host = self.cfg.host
            if not self.host:
                raise Exception("host not set in sxmpp bot - %s" % str(self.cfg))

        self.username = self.user.split('@')[0]
        XMLStream.__init__(self, self.host, self.port, self.name)   
        self.type = 'xmpp'
        self.outqueue = Queue.Queue()
        self.sock = None
        self.me = self.user
        self.jid = self.me
        self.lastin = None
        self.test = 0
        self.password = ""
        self.connecttime = 0
        self.connection = None
        self.privwait = XMPPWait()
        self.errorwait = XMPPErrorWait()
        self.jabber = True
        self.connectok = threading.Event()
        self.jids = {}
        self.topics = {}
        self.timejoined = {}
        self.channels409 = []

        if self.state and not self.state.data.ratelimit:
            self.state.data.ratelimit = 0.05

        if self.port == 0:
            self.port = 5222

    def _resumedata(self):
        """ return data needed for resuming. """
        return {self.name: [self.server, self.user, self.password, self.port]}

    def _outputloop(self):
        """ loop to take care of output to the server. """
        logging.debug('sxmpp - starting outputloop')
        lastsend = time.time()
        charssend = 0
        sleeptime = 0

        while not self.stopped:
            time.sleep(0.01)
            what = self.outqueue.get()

            if self.stopped or what == None:
                 break

            if charssend + len(what) < 1000:
                try:
                    self._raw(what)
                except Exception, ex:
                    self.error = str(ex)
                    handle_exception()
                    continue
                lastsend = time.time()
                charssend += len(what)
            else:
                if time.time() - lastsend > 1:
                    try:
                        self._raw(what)
                    except Exception, ex:
                        handle_exception()
                        continue
                    lastsend = time.time()
                    charssend = len(what)
                    continue
                else:
                    charssend = 0
                    sleeptime = self.cfg['jabberoutsleep']

                if not sleeptime:
                    sleeptime = 1

                logging.info('sxmpp - jabberoutsleep .. sleeping %s seconds' % sleeptime)
                time.sleep(sleeptime)

                try:
                    self._raw(what)
                except Exception, ex:
                    handle_exception()

        logging.debug('sxmpp - stopping outputloop .. %s' % (self.error or 'no error set'))

    def _keepalive(self):

        """ keepalive method .. send empty string to self every 3 minutes. """
        nrsec = 0
        while not self.stopped:
            time.sleep(1)
            nrsec += 1
            if nrsec < 180:
                continue
            else:
                nrsec = 0

            self.sendpresence()

    def sendpresence(self):
        """ send presence based on status and status text set by user. """

        if self.state:
            if self.state.has_key('status') and self.state['status']:
                status = self.state['status']
            else:
                status = ""
            if self.state.has_key('show') and self.state['show']:
                show = self.state['show']
            else:
                show = ""
        else:
            status = ""
            show = ""

        logging.debug('sxmpp - keepalive: %s - %s' % (show, status))

        if show and status:
            p = Presence({'to': self.me, 'show': show, 'status': status})
        elif show:
            p = Presence({'to': self.me, 'show': show })
        elif status:
            p = Presence({'to': self.me, 'status': status})
        else:
            p = Presence({'to': self.me })

        self.send(p)

    def _keepchannelsalive(self):

        """ channels keep alive method. """
        nrsec = 0
        p = Presence({'to': self.me, 'txt': '' })
        while not self.stopped:
            time.sleep(1)
            nrsec += 1
            if nrsec < 600:
                continue
            else:
                nrsec = 0

            for chan in self.state['joinedchannels']:
                if chan not in self.channels409:
                    p = Presence({'to': chan})
                    self.send(p)

    def connect(self, reconnect=True):
        """ connect the xmpp server. """
        if self.stopped:
            logging.warn('sxmpp - bot is stopped .. not connecting')
            return

        try:
            if not XMLStream.connect(self):
                logging.error('sxmpp - connect to %s:%s failed' % (self.host, self.port))
                return
            else:
                logging.warn('sxmpp - connected')
            self.logon(self.cfg.user, self.cfg.password)
            start_new_thread(self._outputloop, ())
            start_new_thread(self._keepalive, ())
            #start_new_thread(self._keepchannelsalive, ())
            self.requestroster()
            self._raw("<presence/>")
            self.connectok.set()
            self.sock.settimeout(None)
            return True
        except Exception, ex:
            handle_exception()
            if reconnect:
                self.reconnect()

    def start(self):
        self.connect()
        BotBase.start(self)

    def logon(self, user, password):
        """ logon on the xmpp server. """
        iq = self.initstream()
        if not self.auth(user, password, iq.id):
            if self.register(user, password):
                time.sleep(5)
                self.auth(user, password)
            else:
                self.exit()
                return
        XMLStream.logon(self)
 
    def initstream(self):
        """ send initial string sequence to the xmpp server. """
        logging.debug('sxmpp - starting initial stream sequence')
        self._raw("""<stream:stream to='%s' xmlns='jabber:client' xmlns:stream='http://etherx.jabber.org/streams'>""" % (self.user.split('@')[1], )) 
        result = self.connection.read()
        iq = self.loop_one(result)
        logging.debug("sxmpp - initstream: %s" % result)
        return iq

    def register(self, jid, password):
        """ register the jid to the server. """
        try:
            resource = jid.split("/")[1]
        except IndexError:
            resource = "jsonbot"
        logging.warn('sxmpp - registering %s' % jid)
        self._raw("""<iq type='get'><query xmlns='jabber:iq:register'/></iq>""")
        result = self.connection.read()
        iq = self.loop_one(result)
        if not iq:
            logging.error("sxmpp - unable to register")
            return
        logging.debug('sxmpp - register: %s' % str(iq))
        self._raw("""<iq type='set'><query xmlns='jabber:iq:register'><username>%s</username><resource>%s</resource><password>%s</password></query></iq>""" % (jid.split('@')[0], resource, password))
        result = self.connection.read()
        logging.debug('sxmpp - register: %s' % result)
        if not result:
            return False
        iq = self.loop_one(result)
        if not iq:
            logging.error("sxmpp - can't decode data: %s" % result)
            return False
        logging.debug('sxmpp - register: %s' % result)
        if iq.error:
            logging.warn('sxmpp - register FAILED - %s' % iq.error)
            if iq.error.code == "405":
                logging.error("sxmpp - this server doesn't allow registration by the bot, you need to create an account for it yourself")
            else:
                logging.error("sxmpp - %s" % xmpperrors[iq.error.code])
            self.error = iq.error
            return False
        logging.warn('sxmpp - register ok')
        return True

    def auth(self, jid, password, digest=""):
        """ auth against the xmpp server. """
        logging.warn('sxmpp - authing %s' % jid)
        name = jid.split('@')[0]
        rsrc = self.cfg['resource'] or self.cfg['resource'] or 'jsonbot';
        self._raw("""<iq type='get'><query xmlns='jabber:iq:auth'><username>%s</username></query></iq>""" % name)
        result = self.connection.read()
        iq = self.loop_one(result)
        logging.debug('sxmpp - auth:' + result)

        if ('digest' in result) and digest:
            s = hashlib.new('SHA1')
            s.update(digest)
            s.update(password)
            d = s.hexdigest()
            self._raw("""<iq type='set'><query xmlns='jabber:iq:auth'><username>%s</username><digest>%s</digest><resource>%s</resource></query></iq>""" % (name, d, rsrc))
        else:
            self._raw("""<iq type='set'><query xmlns='jabber:iq:auth'><username>%s</username><resource>%s</resource><password>%s</password></query></iq>""" % (name, rsrc, password))

        result = self.connection.read()
        iq = self.loop_one(result)
        if not iq:
            logging.error('sxmpp - auth failed: %s' % result)
            return False        

        logging.debug('sxmpp - auth: ' + result)

        if iq.error:
            logging.warn('sxmpp - auth FAILED - %s' % iq.error)
            if iq.error.code == "401":
                logging.warn("sxmpp - wrong user or password")
            else:
                logging.warn("sxmpp - %s" % result)
            self.error = iq.error
            return False

        logging.warn('sxmpp - auth ok')
        return True

    def requestroster(self):
        """ request roster from xmpp server. """
        self._raw("<iq type='get'><query xmlns='jabber:iq:roster'/></iq>")

    def disconnectHandler(self, ex):
        """ disconnect handler. """
        logging.error("sxmpp - disconnected: %s" % str(ex)) 
        if not self.stopped:
            self.reconnect()
        else:
            self.exit()

    def joinchannels(self):
        """ join all already joined channels. """
        for i in self.state['joinedchannels']:
            key = self.channels.getkey(i)
            nick = self.channels.getnick(i)
            result = self.join(i, key, nick)
            if result == 1:
                logging.warn('sxmpp - joined %s' % i)
            else:
                logging.warn('sxmpp - failed to join %s: %s' % (i, result))

    def broadcast(self, txt):
        """ broadcast txt to all joined channels. """
        for i in self.state['joinedchannels']:
            self.say(i, txt)

    def handle_iq(self, data):
        """ iq handler .. overload this when needed. """
        pass

    def handle_message(self, data):
        """ message handler. """
        m = Message(data)
        m.parse(self)
        if m.txt.startswith("{"):
            logging.warn("event is remote")
            m.isremote = True
            gn_callbacks.check(self, m)
            return

        #logging.debug("sxmpp - handling message - %s" % str(m))

        if data.type == 'groupchat' and data.subject:
            logging.debug("checking topic")
            self.topiccheck(m)
            nm = Message(m)
            callbacks.check(self, nm)
            return

        if data.get('x').xmlns == 'jabber:x:delay':
            logging.debug("sxmpp - ignoring delayed message")
            return

        self.privwait.check(m)
        if m.isresponse:
            logging.debug("sxmpp - message is a response")
            return

        if m.groupchat:
            m.msg = False

        jid = None
        m.origjid = m.jid

        for node in m.subelements:
            try:
                m.jid = node.x.item.jid 
            except (AttributeError, TypeError):
                continue

        if self.me in m.fromm:
            logging.debug("message to self .. ignoring")
            return 0
        go = 0

        try:
            cc = self.channels[m.channel]['cc']
        except (TypeError, KeyError):
            cc = self.cfg['defaultcc'] or '!'

        try:
            channick = self.channels[m.channel]['nick']
        except (TypeError, KeyError):
            channick = self.nick

        if m.msg and not self.cfg['noccinmsg']:
            go = 1
        elif not m.txt:
            go = 0
        elif m.txt[0] in cc:
            go = 1
        elif m.txt.startswith("%s: " % channick):
            m.txt = m.txt.replace("%s: " % channick, "")
            go = 1
        elif m.txt.startswith("%s, " % channick):
            m.txt = m.txt.replace("%s, " % channick, "")
            go = 1

        if m.txt and m.txt[0] in cc:
            m.txt = m.txt[1:]

        if go:
            try:
                self.doevent(m)
            except:
                handle_exception()
        else:
            logging.debug("no command in %s" % m.txt)

        try:
            if m.type == 'error':
                if m.code:
                    logging.error('sxmpp.error - ' + str(m))
                self.errorwait.check(m)
                self.errorHandler(m)
        except Exception, ex:
            handle_exception()

        mm = Message(m)
        callbacks.check(self, mm)

    def errorHandler(self, event):
        """ error handler .. calls the errorhandler set in the event. """
        try:
            logging.error("smpp.bot - error occured in %s" % str(event))
            event.errorHandler()
        except AttributeError:
            logging.error('sxmpp - unhandled error: %s' % event)

    def handle_presence(self, data):
        """ presence handler. """
        p = Presence(data)
        frm = p.fromm
        nickk = ""
        nick = p.nick

        if self.me in p.userhost:
            return 0

        if nick:
            self.userhosts[nick] = str(frm)
            nickk = nick

        jid = None

        for node in p.subelements:
            try:
                jid = node.x.item.jid 
            except (AttributeError, TypeError):
                continue

        if nickk and jid:
            channel = p.channel
            if not self.jids.has_key(channel):
                self.jids[channel] = {}
            self.jids[channel][nickk] = jid
            self.userhosts[nickk] = str(jid)
            logging.debug('sxmpp - setting jid of %s (%s) to %s' % (nickk, channel, jid))

        if p.type == 'subscribe':
            pres = Presence({'to': p.fromm, 'type': 'subscribed'})
            self.send(pres)
            pres = Presence({'to': p.fromm, 'type': 'subscribe'})
            self.send(pres)

        nick = p.resource

        if p.type != 'unavailable':
            #self.userchannels.adduniq(nick, p.channel)
            p.joined = True
            p.type = 'available'
        elif self.me in p.userhost:
            try:
                del self.jids[p.channel]
                logging.debug('sxmpp - removed %s channel jids' % p.channel)
            except KeyError:
                pass
        else:
            try:
                del self.jids[p.channel][p.nick]
                logging.debug('sxmpp - removed %s jid' % p.nick)
            except KeyError:
                pass

        pp = Presence(p)
        callbacks.check(self, pp)

        if p.type == 'error':
            for node in p.subelements:
                try:
                    err = node.error.code
                except (AttributeError, TypeError):
                    err = 'no error set'
                try:
                    txt = node.text.data
                except (AttributeError, TypeError):
                    txt = ""
            if err:
                logging.error('sxmpp.error %s: %s'  % (err, txt))

            self.errorwait.check(p)

            try:
                method = getattr(self,'handle_' + err)
                # try to call method
                try:
                    method(p)
                except:
                    handle_exception()
            except AttributeError:
                # no command method to handle event
                pass

    def reconnect(self):
        """ reconnect to the server. """
        if self.stopped:
            logging.warn('sxmpp - bot is stopped .. not reconnecting')
            return

        logging.warn('sxmpp -reconnecting .. sleeping 15 seconds')
        self.exit()
        time.sleep(15)
        newbot = SXMPPBot(self.cfg, self.users, self.plugs, self.jid)

        if newbot.connect():
            self.jid += '.old'
            newbot.joinchannels()
            fleet.replace(self.jid, newbot)
            return True

        return False

    def invite(self, jid):
        pres = Presence({'to': jid, 'type': 'subscribe'})
        self.send(pres)
        time.sleep(2)
        pres = Presence({'to': jid})
        self.send(pres)

    def send(self, what):
        """ send stanza to the server. """
        #logging.warn("sxmpp - send - called from %s" % whichmodule(2))
        if not what:
            logging.debug("sxmpp - can't send empty message")
            return
        try:
            to = what['to']
        except (KeyError, TypeError):
            logging.error("sxmpp - can't determine where to send %s to" % what)
            return

        try:
            jid = JID(to)
        except (InvalidJID, AttributeError):
            logging.error("sxmpp - invalid jid %s .. %s" % (str(to), str(what)))
            return

        try:
            del what['from']
            #del what['fromm']
        except KeyError:
            pass

        try:
            xml = what.toxml()
            if not xml:
                raise Exception("can't convert %s to xml .. bot.send()" % what) 
        except (AttributeError, TypeError):
            handle_exception()
            return
            #raise Exception("can't convert %s to xml .. bot.send()" % what) 
        #logging.warn("sxmpp - to outqueue - %s" % xml)
        self.outqueue.put(xml)
           
    def sendnocb(self, what):
        """ send to server without calling callbacks/monitors. """
        #logging.warn("sxmpp - sendnocb - called from %s" % whichmodule(2))
        try:
            xml = what.toxml()
        except AttributeError:
            xml = what
        self.outqueue.put(xml)

    def action(self, printto, txt, fromm=None, groupchat=True):
        """ send an action. """
        txt = "/me " + txt
        if self.google:
            fromm = self.me
        if printto in self.state['joinedchannels'] and groupchat:
            message = Message({'to': printto, 'txt': txt, 'type': 'groupchat'})
        else:
            message = Message({'to': printto, 'txt': txt})
        if fromm:
            message.fromm = fromm

        self.send(message)
        
    def say(self, printto, txt, event=None, origin="", extend=0, groupchat=False):
        """ say txt to channel/JID. """
        if origin:
            res1, res2 = self.less(origin, txt, 900+extend)        
        else:
            res1, res2 = self.less(printto, txt, 900+extend)        
 
        self.out(printto, res1, event, origin, groupchat)
        if res2:
            self.out(printto, res2, event, origin, groupchat)

    def out(self, printto, txt, event, origin, groupchat):
        if self.google:
            fromm = self.me
        if printto in self.state['joinedchannels'] and groupchat:
            message = Message({'to': printto, 'txt': txt, 'type': 'groupchat'})
        else:
            message = Message({'to': printto, 'txt': txt})
        if origin and '@' in origin:
            message.fromm = origin
        else:
            message.fromm = self.jid

        self.send(message)
        if origin and '@' in origin:
            self.outmonitor(origin, printto, txt, event)
        else:
            self.outmonitor(self.jid, printto, txt, event)

    def saynocb(self, printto, txt, fromm=None, groupchat=True, speed=5, type="normal", how=''):
        """ say txt to channel/JID without calling callbacks/monitors. """
        #txt = jabberstrip(txt)
        if printto in self.state['joinedchannels'] and groupchat:
            message = Message({'to': printto, 'body': txt, 'type': 'groupchat'})
        else:
            message = Message({'to': printto, 'body': txt})
        if fromm:
            message.fromm = fromm
        else:
            message.fromm = self.me

        self.sendnocb(message)

    def userwait(self, msg, txt):
        """ wait for user response. """
        msg.reply(txt)
        queue = Queue.Queue()
        self.privwait.register(msg, queue)
        result = queue.get()
        if result:
            return result.txt

    def save(self):
        """ save bot's state. """
        if self.state:
            self.state.save()

    def quit(self):
        """ send unavailable presence. """
        presence = Presence({'type': 'unavailable' ,'to': self.jid})

        if self.state:
            for i in self.state.data.joinedchannels:
                presence.to = i
                self.send(presence)

        presence = Presence({'type': 'unavailable', 'to': self.jid})
        presence['from'] = self.me
        self.send(presence)
        time.sleep(1)
        
    def exit(self):
        """ exit the bot. """
        self.quit()
        self.stopped = 1
        self.outqueue.put_nowait(None)
        self.save()
        time.sleep(3)
        logging.warn('sxmpp - exit')

    def join(self, channel, password=None, nick=None):
        """ join conference. """
        if channel.startswith("#"):
            return
        try:
            if not nick:
                nick = channel.split('/')[1]
        except IndexError:
            nick = self.nick
        channel = channel.split('/')[0]

        if not self.channels.has_key(channel):
            self.channels.setdefault(channel, {})

        # setup error wait
        q = Queue.Queue()
        self.errorwait.register("409", q, 3)
        self.errorwait.register("401", q, 3)
        self.errorwait.register("400", q, 3)

        # do the actual join
        presence = Presence({'to': channel + '/' + nick})

        if password:
             presence.x.password = password             

        self.send(presence)
        errorobj = waitforqueue(q, 3)

        if errorobj:
            err = errorobj[0].error
            logging.error('sxmpp - error joining %s: %s' % (channel, err))
            if err >= '400':
                if channel not in self.channels409:
                    self.channels409.append(channel)
            return err

        self.timejoined[channel] = time.time()
        chan = self.channels[channel]
        # if password is provided set it
        chan['nick'] = nick

        if password:
            chan['key'] = password

        # check for control char .. if its not there init to !
        if not chan.has_key('cc'):
            chan['cc'] = self.cfg['defaultcc'] or '!'

        if not chan.has_key('perms'):
            chan['perms'] = []

        self.channels.save()

        if channel not in self.state['joinedchannels']:
            self.state['joinedchannels'].append(channel)

        if channel in self.channels409:
            self.channels409.remove(channel)

        self.state.save()
        return 1

    def part(self, channel):
        """ leave conference. """
        if channel.startswith("#"):
            return

        presence = Presence({'to': channel})
        presence.type = 'unavailable'
        self.send(presence)

        if channel in self.state['joinedchannels']:
            self.state['joinedchannels'].remove(channel)

        self.state.save()
        return 1

    def outputnolog(self, printto, what, how, who=None, fromm=None):
        """ do output but don't log it. """
        if fromm:
            return

        self.saynocb(printto, what)

    def topiccheck(self, msg):
        """ check if topic is set. """
        if msg.groupchat:
            try:
                topic = msg.subject
                if not topic:
                    return None
                self.topics[msg.channel] = (topic, msg.userhost, time.time())
                logging.debug('sxmpp -topic of %s set to %s' % (msg.channel, topic))
            except AttributeError:
                return None

    def settopic(self, channel, txt):
        """ set topic. """
        pres = Message({'to': channel, 'subject': txt})
        pres.type = 'groupchat'
        self.send(pres)

    def gettopic(self, channel):
        """ get topic. """
        try:
            topic = self.topics[channel]
            return topic
        except KeyError:
            return None

    def domsg(self, msg):
        """ dispatch an msg on the bot. """

        self.doevent(msg)
