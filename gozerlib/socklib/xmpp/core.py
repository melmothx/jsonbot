# gozerlib/socklib/xmpp/core.py
#
#

"""
    this module contains the core xmpp handling functions.

"""

## gozerlib imports

from gozerlib.eventbase import EventBase
from gozerlib.datadir import datadir
from gozerlib.config import Config
from gozerlib.utils.generic import toenc, jabberstrip, fromenc
from gozerlib.utils.lazydict import LazyDict
from gozerlib.utils.exception import handle_exception
from gozerlib.utils.locking import lockdec
from gozerlib.threads import start_new_thread
from gozerlib.utils.trace import whichmodule

## dom imports

from gozerlib.contrib.xmlstream import NodeBuilder, XMLescape, XMLunescape

## for exceptions

import  xml.parsers.expat

## xmpp imports

from namespace import attributes, subelements

## basic imports

import socket
import os
import time
import copy
import logging
import thread
import cgi

## locks

outlock = thread.allocate_lock()   
inlock = thread.allocate_lock()
connectlock = thread.allocate_lock()
outlocked = lockdec(outlock)
inlocked = lockdec(inlock)  
connectlocked = lockdec(connectlock) 

## classes

class XMLDict(EventBase):


    """
        dictionairy to store xml stanza attributes.

        :params input: optional dict to init with
        :type input: dict

    """

    def __init__(self, input={}):
        if input == None:
            EventBase.__init__(self)
        else:
            EventBase.__init__(self, input)
        try:
            self['fromm'] = self['from']
        except (KeyError, TypeError):
            self['fromm'] = ''

    def __getattr__(self, name):

        """
            override getattribute so nodes in payload can be accessed.

        """

        if not self.has_key(name) and self.has_key('subelements'):

            for i in self['subelements']:

                if name in i:
                    return i[name]

        return LazyDict.__getattr__(self, name, default="")

    def get(self, name):

        """ get a attribute by name. """
        if self.has_key('subelements'):
            for i in self['subelements']:
                if name in i:
                    return i[name]

        if self.has_key(name):
            return self[name]

        return LazyDict()

    def toxml(self):
        """ convert the dictionary to xml. """
        res = dict(self)
        if not res:
            raise Exception("%s .. toxml() can't convert empty dict" % self.name)

        elem = self['element']
        main = "<%s" % self['element']

        for attribute in attributes[elem]: 
            if attribute in res:
                if res[attribute]:
                    main += u" %s='%s'" % (attribute, XMLescape(res[attribute]))
                continue

        main += ">"
        gotsub = False
        if res.has_key('txt'):
            if res['txt']:
                main += u"<body>%s</body>" % XMLescape(res['txt'])
                gotsub = True

        for subelement in subelements[elem]:
            try:
                data = res[subelement]
                if data:
                    main += "<%s>%s</%s>" % (subelement, XMLescape(data), subelement)
                    gotsub = True
            except KeyError:
                pass

        if gotsub:
            main += "</%s>" % elem
        else:
            main = main[:-1]
            main += "/>"

        return main

    def str(self):
        """ convert to string. """
        result = ""
        elem = self['element']
        for item, value in dict(self).iteritems():
            if item in attributes[elem] or item in subelements[elem] or item == 'txt':
                result += "%s='%s' " % (item, value)
        return result
 
class XMLStream(NodeBuilder):

    """
        XMLStream.

        :param host: host to connect to
        :type host: string
        :param port: port to connect to
        :type port: int
        :param name: name of the xmlstream
        :type name: string

    """

    def __init__(self, host, port, name='sxmpp'):
        # start sets these
        self.name = name
        # the connection
        self.connection = None
        self.encoding = "utf-8"
        self.stop = False
        # parse state
        self.result = LazyDict()
        self.final = LazyDict()
        self.subelements = []
        self.reslist = []
        self.cur = u""
        self.tags = []
        self.host = host
        self.port = port
        # handlers
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
        logging.debug("sxmpp.core - proceeding")

    def handle_stream(self, data):
        """ default stream handler. """
        #logging.debug("sxmpp.core - STREAM: %s" % data)

    def handle_streamerror(self, data):
        """ default stream error handler. """
        logging.error("sxmpp.core - STREAMERROR: %s" % data)
        self.exit()

    def handle_streamfeatures(self, data):
        """ default stream features handler. """
        #logging.debug("sxmpp.core - STREAMFEATURES: %s" % data)
         
    def addHandler(self, namespace, func):
        """
            add a namespace handler.

            :param namespace: namespace to register handler for
            :type namespace: string
            :param func: handler function
            :type func: function or method

        """
        self.handlers[namespace] = func

    def delHandler(self, namespace):
        """
            delete a namespace handler.

            :param namespace: namespace to delete handler for
            :type namespace: string

        """
        del self.handlers[namespace]

    def getHandler(self, namespace):
        """
            get a namespace handler.

            :param namespace: namespace get handler for
            :type namespace: string

        """
        try:
            return self.handlers[namespace]
        except KeyError:
            return None

    @inlocked
    def loop_one(self, data):
        """
            handle one xml stanza.

            :param data: data as received on the socket
            :type data: string
            :rtype: gozerbot.utils.lazydict.LazyDict

        """
        NodeBuilder.__init__(self)
        self._dispatch_depth = 2

        try:
            #data = XMLunescape(data.strip())
            self._parser.Parse(data.strip())
        except xml.parsers.expat.ExpatError, ex: 
            if 'not well-formed' in str(ex):  
                logging.error("sxmpp.core - data is not well formed: %s" % data)
                return {}
            logging.debug("sxmpp.core - ALERT: %s - %s" % (str(ex), data))
        except Exception, ex:
            handle_exception()
            return {}

        return self.finish(data)

    def _doprocess(self):
        """ proces all incoming data. """
        logging.debug('starting readloop')
        self.buffer = ""

        while not self.stopped:
            try:
                data = self.connection.read()
                #logging.debug("sxmpp - incoming - %s" % data)
                if data == "":
                    logging.error('remote disconnected')
                    self.error = 'disconnected'
                    self.disconnectHandler(Exception('remote %s disconnected' %  self.host))
                    break
                if data:
                    if not data.endswith(">"):
                        self.buffer += data
                        continue
                    else:
                        self.buffer += data

                    #logging.debug('sxmpp.core - trying: %s' % self.buffer)
                    #buf = XMLunescape(self.buffer)
                    self.loop_one(self.buffer)

            except xml.parsers.expat.ExpatError, ex:
                logging.error("sxmpp.core - %s: %s" % (str(ex), data))
                self.buffer = ""
                self.error = str(ex)
                self.disconnectHandler(ex)
                break

            except Exception, ex:
                handle_exception()
                self.error = str(ex)
                self.disconnectHandler(ex)
                break

        logging.info('sxmpp.core - stopping readloop .. %s' % (self.error or 'error not set'))

    def _raw(self, stanza):
        """ output a xml stanza to the socket. """
        #logging.warn("sxmpp.core - _raw - called from %s" % whichmodule())
        try:
            stanza = stanza.strip()
            if not stanza:
                logging.debug("sxmpp - no stanze provided. called from: %s" % whichmodule())
                return
            if self.stopped:
                logging.debug('sxmpp - bot is stopped .. not sending')
                return

            #what = jabberstrip(stanza)
            what = stanza
            if not what.endswith('>') or not what.startswith('<'):
                logging.error('sxmpp - invalid stanza: %s' % what)
                return
            if what.startswith('<stream') or what.startswith('<message') or what.startswith('<presence') or what.startswith('<iq'):
                logging.debug("_raw: %s" % what)
                try:
                    self.connection.send(what + u"\r\n")
                except AttributeError:
                    self.connection.write(what)
            else:
                logging.error('sxmpp - invalid stanza: %s' % what)

        except socket.error, ex:
            if 'Broken pipe' in str(ex):
                logging.debug('sxmpp.core - broken pipe .. ignoring')
                time.sleep(0.01)
                return
            self.error = str(ex)
            handle_exception()

        except Exception, ex:
            self.error = str(ex)
            handle_exception()

    def connect(self):
        """ connect to the server. """
        if self.stopped:
            logging.warn('sxmpp.core - bot is stopped not connecting to %s' % self.host)
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(30)
        if not self.port:
            self.port = 5222
        if self.server != 'localhost':
            self.host = self.server
        else:
            self.host = self.cfg.host
        logging.warn("sxmpp.core - connecting to %s:%s" % (self.host, self.port))
        self.sock.connect((self.host, self.port))
        self.sock.setblocking(False)
        self.sock.settimeout(60)
        time.sleep(1) 
        logging.debug("sxmpp.core - starting stream")
        self.sock.send('<stream:stream to="%s" xmlns="jabber:client" xmlns:stream="http://etherx.jabber.org/streams" version="1.0">\r\n' % self.user.split('@')[1])
        time.sleep(3)
        result = self.sock.recv(1500)
        logging.debug("sxmpp.core - " + str(result))
        self.loop_one(result)
        self.sock.send('<starttls xmlns="urn:ietf:params:xml:ns:xmpp-tls"/>\r\n')
        time.sleep(3)
        result = self.sock.recv(1500)
        logging.debug("sxmpp.core - " + str(result))
        self.loop_one(result)
        self.sock.settimeout(60)
        return self.dossl()

    def dossl(self):
        """ enable ssl on the socket. """
        try:
            import ssl
            logging.debug("sxmpp.core - wrapping ssl socket")
            self.connection = ssl.wrap_socket(self.sock)
        except ImportError:
            logging.debug("sxmpp.core - making ssl socket")
            self.connection = socket.ssl(self.sock)
        if self.connection:
            return True
        else:
            return False


    def logon(self):
        """ called upon logon on the server. """
        start_new_thread(self._doprocess, ())

    def finish(self, data):
        """
            finish processing of an xml stanza.

            :param data: data which has been used to process the stanza
            :type data: string
            :rtype: gozerbot.utils.lazydict.LazyDict

        """
        methods = []
        self.final['subelements'] = self.subelements

        for subelement in self.subelements:
            logging.debug("sxmpp.core - %s" % str(subelement))
            for elem in subelement:
                logging.debug("setting %s handler" % elem)
                methods.append(self.getHandler(elem))
            for method in methods:
                if not method:
                    continue
                try:
                    result = XMLDict(subelement)
                    result.bot = self
                    result.orig = data
                    result.jabber = True
                    method(result) 
                except Exception, ex:
                    handle_exception()

        if self.tags:
            element = self.tags[0]
            logging.debug("setting element: %s" % element)
        else:
            element = 'stream'

        self.final['element'] = element

        method = self.getHandler(element)

        if method:
            try:
                result = XMLDict(self.final)
                result.bot = self
                result.orig = data
                result.jabber = True
                method(result) 

            except Exception, ex:
                handle_exception()
                result = {}
        else:
            logging.error("sxmpp.core - can't find handler for %s" % element)
            result = {}

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
        if not self.tags:
            self.final.update(attrs)
        else:
            self.result[tag] = attrs
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
            if parentname == 'body':
                self.final['txt'] = data
        attrs = dom.getAttributes()
        ns = dom.getNamespace()
        res[parentname] = LazyDict()
        res[parentname]['data'] = data
        res[parentname].update(attrs) 

        if ns:
            res[parentname]['xmlns'] = ns

        for child in dom.getChildren():  
            name = child.getName()
            data = child.getData()

            if data:
                self.final[name] = data

            attrs = child.getAttributes()
            ns = child.getNamespace()
            res[parentname][name] = LazyDict()
            res[parentname][name]['data'] = data
            res[parentname][name].update(attrs) 
            self.final.update(attrs)

            if ns:
                res[parentname][name]['xmlns'] = ns

        self.subelements.append(res)

    def exit(self):
        """ stop the stream handling. """
        self.stopped = True


    def reconnect(self):
        """ reconnect to the server. """
        logging.warn('reconnecting')
        self.exit()
        logging.warn('sleeping 15 seconds')
        time.sleep(15)
        return self.connect()

    def disconnectHandler(self, ex):
        """
            handler called on disconnect.

            :param ex: exception leading to the disconnect
            :type ex: Exception

        """
        self.stop = True
        logging.warn('disconnected: %s' % str(ex))
        self.reconnect()

