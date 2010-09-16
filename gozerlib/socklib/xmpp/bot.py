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
from gozerlib.callbacks import callbacks, remote_callbacks
from gozerlib.threads import start_new_thread
from gozerlib.fleet import fleet
from gozerlib.botbase import BotBase
from gozerlib.exit import globalshutdown
from gozerlib.channelbase import ChannelBase

## gozerlib.socket imports

from gozerlib.socklib.utils.generic import waitforqueue, jabberstrip, getrandomnick
from gozerlib.utils.generic import toenc, fromenc

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

## SXMPPBot class

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
                raise Exception("%s - host not set - %s" % (self.name, str(self.cfg)))

        self.username = self.user.split('@')[0]
        XMLStream.__init__(self, self.host, self.port, self.name)   
        self.type = 'sxmpp'
        self.outqueue = Queue.Queue()
        self.inqueue = Queue.Queue()
        self.sock = None
        self.me = self.cfg.user
        self.jid = self.me
        self.lastin = None
        self.test = 0
        self.password = ""
        self.connecttime = 0
        self.connection = None
        self.privwait = XMPPWait()
        self.errorwait = XMPPErrorWait()
        self.jabber = True
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

        return {self.name: {
            'type': self.type,
            'nick': self.nick,
            'server': self.server,
            'port': self.port,
            'password': self.password,
            'ipv6': self.ipv6,
            'user': self.user
            }}

    def _outputloop(self):
        """ loop to take care of output to the server. """
        logging.debug('%s - starting outputloop' % self.name)
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
                    break
                lastsend = time.time()
                charssend += len(what)
            else:
                if time.time() - lastsend > 1:
                    try:
                        self._raw(what)
                    except Exception, ex:
                        handle_exception()
                        break
                    lastsend = time.time()
                    charssend = len(what)
                    continue
                else:
                    charssend = 0
                    sleeptime = 0.1 or self.cfg['jabberoutsleep']

                if not sleeptime:
                    sleeptime = 0

                logging.debug('%s - out - sleeping %s seconds' % (self.name, sleeptime))
                time.sleep(sleeptime)

                try:
                    self._raw(toenc(what))
                except Exception, ex:
                    handle_exception()

        logging.debug('%s - stopping outputloop .. %s' % (self.name, self.error or 'no error set'))

        if not self.stopped:
            self.reconnect()

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

        logging.debug('%s - keepalive - %s - %s' % (self.name, show, status))

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
        
        try:
            if not XMLStream.connect(self):
                logging.error('%s - connect to %s:%s failed' % (self.name, self.host, self.port))
                return
            else:
                logging.warn('%s - connected' % self.name)
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
                return self.reconnect()

    def logon(self, user, password):
        """ logon on the xmpp server. """
        iq = self.initstream()
        if not self.auth(user, password, iq.id):
            logging.warn("%s - sleeping 20 seconds before register" % self.name)
            time.sleep(20)
            if self.register(user, password):
                time.sleep(5)
                self.auth(user, password)
            else:
                time.sleep(10)
                self.exit()
                return
        XMLStream.logon(self)
 
    def initstream(self):
        """ send initial string sequence to the xmpp server. """
        logging.debug('%s - starting initial stream sequence' % self.name)
        self._raw("""<stream:stream to='%s' xmlns='jabber:client' xmlns:stream='http://etherx.jabber.org/streams'>""" % (self.user.split('@')[1], )) 
        result = self.connection.read()
        iq = self.loop_one(result)
        logging.debug("%s - initstream - %s" % (self.name, result))
        return iq

    def register(self, jid, password):
        """ register the jid to the server. """
        try:
            resource = jid.split("/")[1]
        except IndexError:
            resource = "jsonbot"
        logging.warn('%s - registering %s' % (self.name, jid))
        self._raw("""<iq type='get'><query xmlns='jabber:iq:register'/></iq>""")
        result = self.connection.read()
        iq = self.loop_one(result)
        if not iq:
            logging.error("%s - unable to register" % self.name)
            return
        logging.debug('%s - register: %s' % (self.name, str(iq)))
        self._raw("""<iq type='set'><query xmlns='jabber:iq:register'><username>%s</username><resource>%s</resource><password>%s</password></query></iq>""" % (jid.split('@')[0], resource, password))
        result = self.connection.read()
        logging.debug('%s - register - %s' % (self.name, result))
        if not result:
            return False
        iq = self.loop_one(result)
        if not iq:
            logging.error("%s - can't decode data - %s" % (self.name, result))
            return False
        logging.debug('sxmpp - register - %s' % result)
        if iq.error:
            logging.warn('%s - register FAILED - %s' % (self.name, iq.error))
            if iq.error.code == "405":
                logging.error("%s - this server doesn't allow registration by the bot, you need to create an account for it yourself" % self.name)
            elif iq.error.code == "500":
                logging.error("%s - %s" % (self.name, iq.error.text.data))
            else:
                logging.error("%s - %s" % (self.name, xmpperrors[iq.error.code]))
            self.error = iq.error
            return False
        logging.warn('%s - register ok' % self.name)
        return True

    def auth(self, jid, password, digest=""):
        """ auth against the xmpp server. """
        logging.warn('%s - authing %s' % (self.name, jid))
        name = jid.split('@')[0]
        rsrc = self.cfg['resource'] or self.cfg['resource'] or 'jsonbot';
        self._raw("""<iq type='get'><query xmlns='jabber:iq:auth'><username>%s</username></query></iq>""" % name)
        result = self.connection.read()
        iq = self.loop_one(result)
        logging.debug('%s - auth - %s' % (self.name, result))

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
            logging.error('%s - auth failed - %s' % (self.name, result))
            return False        

        logging.debug('%s - auth - %s' % (self.name, result))

        if iq.error:
            logging.warn('%s - auth failed - %s' % (self.name, iq.error))
            if iq.error.code == "401":
                logging.warn("%s - wrong user or password" % self.name)
            else:
                logging.warn("%s - %s" % (self.name, result))
            self.error = iq.error
            return False

        logging.warn('%s - auth ok' % self.name)
        return True

    def requestroster(self):
        """ request roster from xmpp server. """
        self._raw("<iq type='get'><query xmlns='jabber:iq:roster'/></iq>")

    def disconnectHandler(self, ex):
        """ disconnect handler. """
        self.reconnect()

    def joinchannels(self):
        """ join all already joined channels. """
        for i in self.state['joinedchannels']:
            chan = ChannelBase(i)
            key = chan.data.key or None
            nick = chan.data.nick or "jsonbot"
            result = self.join(i, key, nick)
            if result == 1:
                logging.warn('%s - joined %s' % (self.name, i))
            else:
                logging.warn('%s - failed to join %s: %s' % (self.name, i, result))

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

        if data.type == 'groupchat' and data.subject:
            logging.debug("%s - checking topic" % self.name)
            self.topiccheck(m)
            nm = Message(m)
            callbacks.check(self, nm)
            return

        if data.get('x').xmlns == 'jabber:x:delay':
            logging.warn("%s - ignoring delayed message" % self.name)
            return

        self.privwait.check(m)
        if m.isresponse:
            logging.debug("%s - message is a response" % self.name)
            return

        jid = None
        m.origjid = m.jid

        for node in m.subelements:
            try:
                m.jid = node.x.item.jid 
            except (AttributeError, TypeError):
                continue

        if self.me in m.fromm:
            logging.debug("%s - message to self .. ignoring" % self.name)
            return 0

        try:
            if m.type == 'error':
                if m.code:
                    logging.error('%s - error - %s' % (self.name, str(m)))
                self.errorwait.check(m)
                self.errorHandler(m)
        except Exception, ex:
            handle_exception()

        self.put(m)

    def errorHandler(self, event):
        """ error handler .. calls the errorhandler set in the event. """
        try:
            logging.error("%s - error occured in %s" % (self.name, event.dump()))
            event.errorHandler()
        except AttributeError:
            logging.error('%s - unhandled error - %s' % (self.name, event.dump()))

    def handle_presence(self, data):
        """ presence handler. """
        p = Presence(data)
        p.parse()
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
            logging.debug('%s - setting jid of %s (%s) to %s' % (self.name, nickk, channel, jid))

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
                logging.debug('%s - removed %s channel jids' % (self.name, p.channel))
            except KeyError:
                pass
        else:
            try:
                del self.jids[p.channel][p.nick]
                logging.debug('%s - removed %s jid' % (self.name, p.nick))
            except KeyError:
                pass

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
                logging.error('%s - error - %s - %s'  % (self.name, err, txt))

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

        self.doevent(p)

    def invite(self, jid):
        pres = Presence({'to': jid, 'type': 'subscribe'})
        self.send(pres)
        time.sleep(2)
        pres = Presence({'to': jid})
        self.send(pres)

    def send(self, what):
        """ send stanza to the server. """
        if not what:
            logging.debug("%s - can't send empty message" % self.name)
            return
        try:
            to = what['to']
        except (KeyError, TypeError):
            logging.error("%s - can't determine where to send %s to" % (self.name, what))
            return

        try:
            jid = JID(to)
        except (InvalidJID, AttributeError):
            logging.error("%s - invalid jid - %s - %s" % (self.name, str(to), str(what)))
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

        self.outqueue.put(xml)
           
    def sendnocb(self, what):
        """ send to server without calling callbacks/monitors. """
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
        self.fromm = origin or self.userhost
        if origin:
            res1, res2 = self.less(origin, txt, 900+extend)        
        else:
            res1, res2 = self.less(printto, txt, 900+extend)        
 
        if res1:
            self.out(printto, res1, event, origin, groupchat)

    def out(self, printto, txt, event, origin, groupchat):
        self.outnocb(printto, txt, event, origin, groupchat)
        if origin and '@' in origin:
            self.outmonitor(origin, printto, txt, event)
        else:
            self.outmonitor(self.jid, printto, txt, event)

    def saynocb(self, printto, txt, event=None, origin="", extend=0, groupchat=False):
        """ say txt to channel/JID. """
        if origin:
            res1, res2 = self.less(origin, txt, 900+extend)        
        else:
            res1, res2 = self.less(printto, txt, 900+extend)        
 
        self.outnocb(printto, res1, event, origin, groupchat)

    def outnocb(self, printto, txt, event=None, origin=None, groupchat=False):
        #txt = self.normalize(txt)
        if self.google:
            fromm = self.me
        if printto in self.state['joinedchannels'] or groupchat:
            message = Message({'to': printto, 'txt': txt, 'type': 'groupchat'})
        else:
            message = Message({'to': printto, 'txt': txt})
        if origin and '@' in origin:
            message.fromm = origin
        else:
            message.fromm = self.jid

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

    def shutdown(self):
        #self.quit()
        self.outqueue.put_nowait(None)

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
            logging.error('%s - error joining %s - %s' % (self.name, channel, err))
            if err >= '400':
                if channel not in self.channels409:
                    self.channels409.append(channel)
            return err

        self.timejoined[channel] = time.time()
        chan = ChannelBase(channel)
        # if password is provided set it
        chan.data['nick'] = nick

        if password:
            chan.data['key'] = password

        # check for control char .. if its not there init to !
        if not chan.data.has_key('cc'):
            chan.data['cc'] = self.cfg['defaultcc'] or '!'

        if channel not in self.state['joinedchannels']:
            self.state['joinedchannels'].append(channel)
            self.state.save()

        if channel in self.channels409:
            self.channels409.remove(channel)

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
                logging.debug('%s - topic of %s set to %s' % (self.name, msg.channel, topic))
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

    def normalize(self, what):
        what = what.replace("<b>", "")
        what = what.replace("</b>", "")
        what = what.replace("&lt;b&gt;", "")
        what = what.replace("&lt;/b&gt;", "")
        what = what.replace("<i>", "")
        what = what.replace("</i>", "")
        what = what.replace("&lt;i&gt;", "")
        what = what.replace("&lt;/i&gt;", "")
        return what
