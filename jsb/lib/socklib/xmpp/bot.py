# jsb/socklib/xmpp/bot.py
#
#

""" jabber bot definition """

## jsb imports

from jsb.lib.users import users
from jsb.utils.exception import handle_exception
from jsb.utils.trace import whichmodule
from jsb.utils.locking import lockdec
from jsb.utils.pdod import Pdod
from jsb.utils.dol import Dol
from jsb.lib.less import Less
from jsb.lib.callbacks import callbacks, remote_callbacks
from jsb.lib.threads import start_new_thread
from jsb.lib.botbase import BotBase
from jsb.lib.exit import globalshutdown
from jsb.lib.channelbase import ChannelBase
from jsb.lib.fleet import getfleet

## jsb.socket imports

from jsb.lib.socklib.utils.generic import waitforqueue, jabberstrip, getrandomnick
from jsb.utils.generic import toenc, fromenc

## xmpp imports

from jsb.contrib.xmlstream import XMLescape, XMLunescape
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
import cgi

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
            if not self.host: raise Exception("%s - host not set - %s" % (self.name, str(self.cfg)))
        self.username = self.user.split('@')[0]
        XMLStream.__init__(self, self.host, self.port, self.name)   
        self.type = 'sxmpp'
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
        if self.state and not self.state.data.ratelimit: self.state.data.ratelimit = 0.05
        if self.port == 0: self.port = 5222

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

    def _keepalive(self):
        """ keepalive method .. send empty string to self every 3 minutes. """
        nrsec = 0
        while not self.stopped:
            time.sleep(1)
            nrsec += 1
            if nrsec < 180: continue
            else: nrsec = 0
            self.sendpresence()

    def sendpresence(self):
        """ send presence based on status and status text set by user. """
        if self.state:
            if self.state.has_key('status') and self.state['status']: status = self.state['status']
            else: status = ""
            if self.state.has_key('show') and self.state['show']: show = self.state['show']
            else: show = ""
        else:
            status = ""
            show = ""
        logging.debug('%s - keepalive - %s - %s' % (self.name, show, status))
        if show and status: p = Presence({'to': self.me, 'show': show, 'status': status})
        elif show: p = Presence({'to': self.me, 'show': show })
        elif status: p = Presence({'to': self.me, 'status': status})
        else: p = Presence({'to': self.me })
        self.send(p)

    def _keepchannelsalive(self):
        """ channels keep alive method. """
        nrsec = 0
        p = Presence({'to': self.me, 'txt': '' })
        while not self.stopped:
            time.sleep(1)
            nrsec += 1
            if nrsec < 600: continue
            else: nrsec = 0
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
            else: logging.warn('%s - connected' % self.name)
            self.logon(self.cfg.user, self.cfg.password)
            start_new_thread(self._keepalive, ())
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
        if not iq: logging.error("sxmpp - cannot init stream") ; return
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
        try: resource = jid.split("/")[1]
        except IndexError: resource = "jsb"
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
        if not result: return False
        iq = self.loop_one(result)
        if not iq:
            logging.error("%s - can't decode data - %s" % (self.name, result))
            return False
        logging.debug('sxmpp - register - %s' % result)
        if iq.error:
            logging.warn('%s - register FAILED - %s' % (self.name, iq.error))
            if not iq.error.code: logging.error("%s - can't determine error code" % self.name) ; return False
            if iq.error.code == "405": logging.error("%s - this server doesn't allow registration by the bot, you need to create an account for it yourself" % self.name)
            elif iq.error.code == "500": logging.error("%s - %s - %s" % (self.name, iq.error.code, iq.error.text))
            else: logging.error("%s - %s" % (self.name, xmpperrors[iq.error.code]))
            self.error = iq.error
            return False
        logging.warn('%s - register ok' % self.name)
        return True

    def auth(self, jid, password, digest=""):
        """ auth against the xmpp server. """
        logging.warn('%s - authing %s' % (self.name, jid))
        name = jid.split('@')[0]
        rsrc = self.cfg['resource'] or self.cfg['resource'] or 'jsb';
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
        else: self._raw("""<iq type='set'><query xmlns='jabber:iq:auth'><username>%s</username><resource>%s</resource><password>%s</password></query></iq>""" % (name, rsrc, password))
        result = self.connection.read()
        iq = self.loop_one(result)
        if not iq:
            logging.error('%s - auth failed - %s' % (self.name, result))
            return False        
        logging.debug('%s - auth - %s' % (self.name, result))
        if iq.error:
            logging.warn('%s - auth failed - %s' % (self.name, iq.error.code))
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

    def outnocb(self, printto, txt, how=None, event=None, html=False, *args, **kwargs):
        """ output txt to bot. """
        if printto and printto in self.state['joinedchannels']: outtype = 'groupchat'
        else: outtype = "chat"
        target = printto
        if not html: 
            txt = self.normalize(txt)
        repl = Message({'from': self.me, 'to': target, 'type': outtype, 'txt': txt})
        if html:
            repl.html = txt
        if not repl.type: repl.type = 'normal'
        logging.debug("%s - sxmpp - out - %s - %s" % (self.name, printto, unicode(txt)))
        self.send(repl)

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
            try: m.jid = node.x.item.jid 
            except (AttributeError, TypeError): continue
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
        except AttributeError: logging.error('%s - unhandled error - %s' % (self.name, event.dump()))

    def handle_presence(self, data):
        """ presence handler. """
        p = Presence(data)
        p.parse()
        frm = p.fromm
        nickk = ""
        nick = p.nick
        if self.me in p.userhost: return 0
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
                try:
                    method(p)
                except:
                    handle_exception()
            except AttributeError:
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
        try: del what['from']
        except KeyError: pass
        try:
            xml = what.tojabber()
            if not xml:
                raise Exception("can't convert %s to xml .. bot.send()" % what) 
        except (AttributeError, TypeError):
            handle_exception()
            return
        if not self.checkifvalid(xml): logging.error("%s - NOT PROPER XML - %s" % (self.name, xml))
        else: self._raw(xml)
           
    def action(self, printto, txt, fromm=None, groupchat=True):
        """ send an action. """
        txt = "/me " + txt
        if self.google:
            fromm = self.me
        if printto in self.state['joinedchannels'] and groupchat:
            message = Message({'to': printto, 'txt': txt, 'type': 'groupchat'})
        else: message = Message({'to': printto, 'txt': txt})
        if fromm: message.fromm = fromm
        self.send(message)
        
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
        if self.error: return
        presence = Presence({'type': 'unavailable' ,'to': self.jid})
        if self.state:
            for i in self.state.data.joinedchannels:
                presence.to = i
                self.send(presence)
        presence = Presence({'type': 'unavailable', 'to': self.jid})
        presence['from'] = self.me
        self.send(presence)

    def shutdown(self):
        self.outqueue.put_nowait(None)

    def join(self, channel, password=None, nick=None):
        """ join conference. """
        if channel.startswith("#"): return
        try:
            if not nick: nick = channel.split('/')[1]
        except IndexError: nick = self.nick
        channel = channel.split('/')[0]
        q = Queue.Queue()
        self.errorwait.register("409", q, 3)
        self.errorwait.register("401", q, 3)
        self.errorwait.register("400", q, 3)
        presence = Presence({'to': channel + '/' + nick})
        if password:
             presence.x.password = password             
        self.send(presence)
        errorobj = waitforqueue(q, 3)
        if errorobj:
            err = errorobj[0].error
            logging.error('%s - error joining %s - %s' % (self.name, channel, err))
            if err >= '400':
                if channel not in self.channels409: self.channels409.append(channel)
            return err
        self.timejoined[channel] = time.time()
        chan = ChannelBase(channel, self.botname)
        chan.data['nick'] = nick
        if password:
            chan.data['key'] = password
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
        if channel.startswith("#"): return
        presence = Presence({'to': channel})
        presence.type = 'unavailable'
        self.send(presence)
        if channel in self.state['joinedchannels']: self.state['joinedchannels'].remove(channel)
        self.state.save()
        return 1

    def outputnolog(self, printto, what, how, who=None, fromm=None):
        """ do output but don't log it. """
        if fromm: return
        self.saynocb(printto, what)

    def topiccheck(self, msg):
        """ check if topic is set. """
        if msg.groupchat:
            try:
                topic = msg.subject
                if not topic: return None
                self.topics[msg.channel] = (topic, msg.userhost, time.time())
                logging.debug('%s - topic of %s set to %s' % (self.name, msg.channel, topic))
            except AttributeError: return None

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
        except KeyError: return None

    def domsg(self, msg):
        """ dispatch an msg on the bot. """
        self.doevent(msg)

    def normalize(self, what):
        #what = cgi.escape(what)
        what = what.replace("\002", "")
        what = what.replace("<b>", "")
        what = what.replace("</b>", "")
        what = what.replace("&lt;b&gt;", "")
        what = what.replace("&lt;/b&gt;", "")
        what = what.replace("<i>", "")
        what = what.replace("</i>", "")
        what = what.replace("&lt;i&gt;", "")
        what = what.replace("&lt;/i&gt;", "")
        return what

    def doreconnect(self):
        """ reconnect to the server. """
        botjid = self.jid
        newbot = getfleet().makebot('sxmpp', self.name, cfg=self.cfg)
        newbot.reconnectcount = self.reconnectcount
        self.exit()
        if newbot.start():
            self.jid += '.old'
            #newbot.joinchannels()
            if fleet.replace(botjid, newbot): return True
        return False

