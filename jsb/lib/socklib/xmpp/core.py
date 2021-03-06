# jsb/socklib/xmpp/core.py
#
#

"""
    this module contains the core xmpp handling functions.

"""

## jsb imports

from jsb.lib.eventbase import EventBase
from jsb.lib.config import Config
from jsb.utils.generic import toenc, jabberstrip, fromenc
from jsb.utils.lazydict import LazyDict
from jsb.utils.exception import handle_exception
from jsb.utils.locking import lockdec
from jsb.lib.threads import start_new_thread
from jsb.utils.trace import whichmodule
from jsb.lib.gozerevent import GozerEvent
from jsb.lib.fleet import getfleet

## xmpp import

from jsb.contrib.xmlstream import NodeBuilder, XMLescape, XMLunescape

## basic imports

import socket
import os
import time
import copy
import logging
import thread
import cgi
import xml

## locks

outlock = thread.allocate_lock()   
inlock = thread.allocate_lock()
connectlock = thread.allocate_lock()
outlocked = lockdec(outlock)
inlocked = lockdec(inlock)  
connectlocked = lockdec(connectlock) 

## classes

class XMLStream(NodeBuilder):

    """ XMLStream. """

    def __init__(self, host, port, name='sxmpp'):
        self.name = name
        self.connection = None
        self.encoding = "utf-8"
        self.stop = False
        self.result = LazyDict()
        self.final = LazyDict()
        self.subelements = []
        self.reslist = []
        self.cur = u""
        self.tags = []
        self.host = host
        self.port = port
        self.handlers = LazyDict()
        self.addHandler('proceed', self.handle_proceed)
        self.addHandler('message', self.handle_message)
        self.addHandler('presence', self.handle_presence)
        self.addHandler('iq', self.handle_iq)
        self.addHandler('stream', self.handle_stream)
        self.addHandler('stream:stream', self.handle_stream)
        self.addHandler('stream:error', self.handle_streamerror)
        self.addHandler('stream:features', self.handle_streamfeatures)

    def handle_proceed(self, data):
        """ default stream handler. """
        logging.debug("%s - proceeding" % self.name)

    def handle_stream(self, data):
        """ default stream handler. """
        logging.info("%s - stream - %s" % (self.name, data.dump()))

    def handle_streamend(self, data):
        """ default stream handler. """
        logging.warn("%s - stream END - %s" % (self.name, data))
        
    def handle_streamerror(self, data):
        """ default stream error handler. """
        logging.error("%s - STREAMERROR - %s" % (self.name, data.dump()))
 
    def handle_streamfeatures(self, data):
        """ default stream features handler. """
        logging.debug("%s - STREAMFEATURES: %s" % (self.name, LazyDict(data).dump()))
         
    def addHandler(self, namespace, func):
        """ add a namespace handler. """
        self.handlers[namespace] = func

    def delHandler(self, namespace):
        """ delete a namespace handler. """
        del self.handlers[namespace]

    def getHandler(self, namespace):
        """ get a namespace handler. """
        try: return self.handlers[namespace]
        except KeyError: return None

    def parse_one(self, data):
        """ handle one xml stanza. """
        NodeBuilder.__init__(self)
        self._dispatch_depth = 2
        try: return self._parser.Parse(data.strip())
        except xml.parsers.expat.ExpatError, ex: 
            if 'not well-formed' in str(ex):  
                logging.error("%s - data is not well formed" % self.name)
                logging.debug(data)
                handle_exception()
                logging.debug("buffer: %s previous: %s" % (self.buffer, self.prevbuffer))
                return {}
            logging.debug("%s - ALERT: %s - %s" % (self.name, str(ex), data))
        except Exception, ex:
            handle_exception()
            return {}

    def checkifvalid(self, data):
        result = self.parse_one(data)
        self.final = {}
        self.reslist = []
        self.tags = []
        self.subelements = []
        #self.buffer = ""
        return result

    @inlocked
    def loop_one(self, data):
        """ handle one xml stanza. """
        if self.parse_one(data): return self.finish(data)
        return {}

    def _readloop(self):
        """ proces all incoming data. """
        logging.debug('%s - starting readloop' % self.name)
        self.prevbuffer = ""
        self.buffer = ""
        self.error = ""
        data = ""
        while not self.stopped:
            time.sleep(0.001)
            try:
                data = jabberstrip(fromenc(self.connection.read()))
                logging.debug(u"%s - incoming: %s" % (self.name, data))
                if data.endswith("</stream:stream>"):
                    logging.error("%s - end of stream detected" % self.name)
                    self.error = "streamend"
                    self.disconnectHandler(Exception('remote %s disconnected' %  self.host))
                    break
                if data == "":
                    logging.error('%s - remote disconnected' % self.name)
                    self.error = 'disconnected'
                    self.disconnectHandler(Exception('remote %s disconnected' %  self.host))
                    break
                if True:
                    self.buffer = u"%s%s" % (self.buffer, data)
                    #splitted = self.buffer.split(">")
                    #lastitem = splitted[-1]
                    handlers = self.handlers.keys()
                    handlers.append("/")
                    for handler in handlers:
                        target = "%s>" % handler
                        index = self.buffer.find(target)
                        if index != -1:
                            try:
                                if self.loop_one(self.buffer[:index+len(target)]):
                                    self.buffer = self.buffer[index+1+len(target):]
                                else:
                                    self.buffer = ""
                                    break
                            except: handle_exception()
            except xml.parsers.expat.ExpatError, ex:
                logging.error("%s - %s - %s" % (self.name, str(ex), data))
                self.buffer = ""
                self.error = str(ex)
                self.disconnectHandler(ex)
                break
            except Exception, ex:
                handle_exception()
                self.error = str(ex)
                self.disconnectHandler(ex)
                break
        logging.info('%s - stopping readloop .. %s' % (self.name, self.error or 'error not set'))

    @outlocked
    def _raw(self, stanza):
        """ output a xml stanza to the socket. """
        if not self.connection: return
        time.sleep(0.01)
        try:
            stanza = stanza.strip()
            if not stanza:
                logging.debug("%s - no stanze provided. called from: %s" % (self.name, whichmodule()))
                return
            what = jabberstrip(stanza)
            what = toenc(stanza)
            logging.debug("%s - out - %s" % (self.name, what))             
            if not what.endswith('>') or not what.startswith('<'):
                logging.error('%s - invalid stanza: %s' % (self.name, what))
                return
            if what.startswith('<stream') or what.startswith('<message') or what.startswith('<presence') or what.startswith('<iq'):
                logging.debug(u"%s - sxmpp - out - %s" % (self.name, what))
                try: self.connection.send(what + u"\r\n")
                except AttributeError: self.connection.write(what)
            else: logging.error('%s - invalid stanza: %s' % (self.name, what))
        except socket.error, ex:
            if 'Broken pipe' in str(ex):
                logging.debug('%s - core - broken pipe .. ignoring' % self.name)
                return
            self.error = str(ex)
            handle_exception()
        except Exception, ex:
            self.error = str(ex)
            handle_exception()

    def connect(self):
        """ connect to the server. """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        self.sock.settimeout(10)
        if not self.port: self.port = 5222
        if self.server != 'localhost': self.host = self.server
        else: self.host = self.cfg.host
        logging.warn("%s - connecting to %s:%s" % (self.name, self.host, self.port))
        self.sock.connect((self.host, self.port))
        self.sock.settimeout(60)
        time.sleep(1) 
        logging.debug("%s - starting stream" % self.name)
        self.sock.send('<stream:stream to="%s" xmlns="jabber:client" xmlns:stream="http://etherx.jabber.org/streams" version="1.0">\r\n' % self.user.split('@')[1])
        time.sleep(3)
        result = self.sock.recv(1500)
        logging.debug("%s - %s" %  (self.name, str(result)))
        self.loop_one(result)
        self.sock.send('<starttls xmlns="urn:ietf:params:xml:ns:xmpp-tls"/>\r\n')
        time.sleep(3)
        result = self.sock.recv(1500)
        logging.debug("%s - %s" % (self.name, str(result)))
        self.loop_one(result)
        self.sock.settimeout(60)
        self.sock.setblocking(1)
        return self.dossl()

    def dossl(self):
        """ enable ssl on the socket. """
        try:
            import ssl
            logging.debug("%s - wrapping ssl socket" % self.name)
            self.connection = ssl.wrap_socket(self.sock)
        except ImportError:
            logging.debug("%s - making ssl socket" % self.name)
            self.connection = socket.ssl(self.sock)
        if self.connection:
            return True
        else:
            return False

    def logon(self):
        """ called upon logon on the server. """
        start_new_thread(self._doprocess, ())

    def finish(self, data):
        """ finish processing of an xml stanza. """
        methods = []
        self.final['subelements'] = self.subelements
        for subelement in self.subelements:
            logging.debug("%s - %s" % (self.name, str(subelement)))
            for elem in subelement:
                logging.debug("%s - setting %s handler" % (self.name, elem))
                methods.append(self.getHandler(elem))
            for method in methods:
                if not method: continue
                try:
                    result = GozerEvent(subelement)
                    result.bot = self
                    result.orig = data
                    result.jabber = True
                    method(result) 
                except Exception, ex: handle_exception()
        if self.tags:
            element = self.tags[0]
            logging.debug("%s - setting element: %s" % (self.name, element))
        else: element = 'stream'
        self.final['element'] = element
        method = self.getHandler(element)
        if method:
            try:
                result = GozerEvent(self.final)
                result.bot = self
                result.orig = data
                result.jabber = True
                method(result) 
            except Exception, ex:
                handle_exception()
                result = {}
        else:
            logging.error("%s - can't find handler for %s" % (self.name, element))
            result = {}
        if result:
            self.final = {}
            self.reslist = []
            self.tags = []
            self.subelements = []
            self.buffer = ""
            return result

    def unknown_starttag(self,  tag, attrs):
        """ handler called by the self._parser on start of a unknown start tag. """
        NodeBuilder.unknown_starttag(self, tag, attrs)
        self.cur = tag
        if not self.tags: self.final.update(attrs)
        else: self.result[tag] = attrs
        self.tags.append(tag)
 
    def unknown_endtag(self,  tag):
        """ handler called by the self._parser on start of a unknown endtag. """
        NodeBuilder.unknown_endtag(self, tag)
        self.result = {}
        self.cur = u""
        
    def handle_data(self, data):
        """ node data handler. """
        NodeBuilder.handle_data(self, data)

    def dispatch(self, dom):
        """ dispatch a dom to the appropiate handler. """
        res = LazyDict()
        parentname = dom.getName()
        data = dom.getData()
        if data:
            self.final[parentname] = data
            if parentname == 'body': self.final['txt'] = data
        attrs = dom.getAttributes()
        ns = dom.getNamespace()
        res[parentname] = LazyDict()
        res[parentname]['data'] = data
        res[parentname].update(attrs) 
        if ns: res[parentname]['xmlns'] = ns
        for child in dom.getChildren():  
            name = child.getName()
            data = child.getData()
            if data: self.final[name] = data
            attrs = child.getAttributes()
            ns = child.getNamespace()
            res[parentname][name] = LazyDict()
            res[parentname][name]['data'] = data
            res[parentname][name].update(attrs) 
            self.final.update(attrs)
            if ns: res[parentname][name]['xmlns'] = ns
        self.subelements.append(res)

    def disconnectHandler(self, ex):
        """ handler called on disconnect. """
        self.stopped = True
        logging.warn('%s - disconnected: %s' % (self.name, str(ex)))
