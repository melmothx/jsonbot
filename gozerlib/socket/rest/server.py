# gozerbot/rest/server.py
#
#

## gozerlib imports

from gozerlib.utils.exception import handle_exception, exceptionmsg
from gozerlib.utils.trace import calledfrom
from gozerlib.config import cfg as config
from gozerlib.persiststate import ObjectState
from gozerlib.threads import start_new_thread

# basic imports

from SocketServer import BaseServer, ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urllib import unquote_plus
from asyncore import dispatcher
from cgi import escape
import time
import sys
import select
import types
import socket
import logging

class RestServerBase(HTTPServer):

    """ REST web server """

    allow_reuse_address = True
    daemon_thread = True

    def start(self):
        self.name = calledfrom(sys._getframe(0))
        self.stop = False
        self.running = False
        self.handlers = {}
        self.webmods = {}
        self.state = ObjectState()
        self.state.define('whitelistenable', 0)
        self.state.define('whitelist', [])
        self.state.define('blacklist', [])
        self.state.define('disable', [])
        self.poll = select.poll()
        self.poll.register(self)
        start_new_thread(self.serve, ())

    def shutdown(self):
        try:
            self.stop = True
            #self.socket.shutdown(2)
            #self.socket.close()
            time.sleep(0.2)
            self.server_close()
        except Exception, ex:
            handle_exception()

    def serve(self):
        logging.warn('rest.server - starting')
        time.sleep(1)
        while not self.stop:
            self.running = True
            try:
                got = self.poll.poll(100)
            except Exception, ex:
                handle_exception()
            if got and not self.stop:
                try:
                    self.handle_request()
                except Exception, ex:
                    handle_exception()
            time.sleep(0.01)
        self.running = False
        logging.warn('rest.server - stopping')

    def entrypoint(self, request):
        ip = request.ip
        if not self.whitelistenable() and ip in self.blacklist():
            logging.warn('rest.server - denied %s' % ip)
            request.send_error(401)
            return False
        if  self.whitelistenable() and ip not in self.whitelist():
            logging.warn('rest.server - denied %s' % ip)
            request.send_error(401)
            return False
        return True

    def whitelistenable(self): 
        return self.state['whitelistenable']

    def whitelist(self): 
        return self.state['whitelist']

    def blacklist(self): 
        return self.state['blacklist']

    def addhandler(self, path, type, handler):
        """ add a web handler """
        splitted = []
        for i in path.split('/'):
            if i:
                splitted.append(i)
        splitted = tuple(splitted)
        if not self.handlers.has_key(splitted):
            self.handlers[splitted] = {}
        self.handlers[splitted][type] = handler
        logging.info('rest.server - %s %s handler added' % (splitted, type))

    def enable(self, what):
        try:
            self.state['disable'].remove(what)
            logging.info('rest.server - enabled %s' % str(what))
        except ValueError:
            pass

    def disable(self, what):
        self.state['disable'].append(what)
        logging.info('rest.server - disabled %s' % str(what))

    def do(self, request):
        """ do a request """
        path = request.path.split('?')[0]
        if path.endswith('/'):
            path = path[:-1]
        splitted = []
        for i in path.split('/'):
            if i:
                splitted.append(i)
        splitted = tuple(splitted)
        for i in self.state['disable']:
            if i in splitted:
                logging.warn('rest.server - %s - denied disabled %s' % (request.ip, i))
                request.send_error(404)
                return
        request.splitted = splitted
        request.value = None
        type = request.command
        try:
            func = self.handlers[splitted][type]
        except (KeyError, ValueError):
            try:
                func = self.handlers[splitted[:-1]][type]
                request.value = splitted[-1]
            except (KeyError, ValueError):
                request.send_error(404)
                return
        result = func(self, request)
        logging.info('rest.server - %s - result: %s' % (request.ip, str(result)))
        return result

    def handle_error(self, request, addr):
        """ log the error """
        ip = request.ip
        exctype, excvalue, tb = sys.exc_info()
        if exctype == socket.timeout:
            logging.warn('rest.server - %s - socket timeout' % (ip, ))
            return
        if exctype == socket.error:
            logging.warn('rest.server - %s - socket error: %s' % (ip, excvalue))
            return
        exceptstr = exceptionmsg()
        logging.warn('rest.server - %s - error %s %s => %s' % (ip, exctype, excvalue, exceptstr))


class RestServer(ThreadingMixIn, RestServerBase):

    pass

class RestServerAsync(RestServerBase, dispatcher):

    pass

class RestRequestHandler(BaseHTTPRequestHandler):

    """ timeserver request handler class """

    def setup(self):
        BaseHTTPRequestHandler.setup(self)
        self.ip = self.client_address[0]
        self.name = self.ip
        self.size = 0

    def writeheader(self, type='text/plain'):
        self.send_response(200)
        self.send_header('Content-type', '%s; charset=%s ' % (type,sys.getdefaultencoding()))
        self.send_header('Server', config['version'])
        self.end_headers()

    def sendresult(self):
        try:
            result = self.server.do(self)
            if not result:
                return
            self.size = len(result)
        except Exception, ex:
            handle_exception()
            self.send_error(501)
            return
        self.writeheader()
        self.wfile.write(result)
        self.wfile.close()

    def handle_request(self):
        if not self.server.entrypoint(self):
            return
        self.sendresult()

    do_DELETE = do_PUT = do_GET = do_POST = handle_request

    def log_request(self, code):
        """ log the request """
        try:
            ua = self.headers['user-agent']
        except:
            ua = "-"
        try:
            rf = self.headers['referer']
        except:
            rf = "-"

        if hasattr(self, 'path'):
            logging.debug('rest.server - %s "%s %s %s" %s %s "%s" "%s"' % (self.address_string(), self.command, self.path, self.request_version, code, self.size, rf, ua))
        else:
            logging.debug('rest.server - %s "%s %s %s" %s %s "%s" "%s"' % (self.address_string(), self.command, "none", self.request_version, code, self.size, rf, ua))

class SecureRestServer(RestServer):

    def __init__(self, server_address, HandlerClass, keyfile, certfile):
        from OpenSSL import SSL
        BaseServer.__init__(self, server_address, HandlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.set_options(SSL.OP_NO_SSLv2)
        logging.warn("rest.server - loading private key from %s" % keyfile)
        ctx.use_privatekey_file (keyfile)
        logging.warn('rest.server - loading certificate from %s' % certfile)
        ctx.use_certificate_file(certfile)
        logging.info('rest.server - creating SSL socket on %s' % str(server_address))
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                        self.socket_type))
        self.server_bind()  
        self.server_activate()

class SecureAuthRestServer(SecureRestServer):

    def __init__(self, server_address, HandlerClass, chain, serverkey, servercert):
        from OpenSSL import SSL
        BaseServer.__init__(self, server_address, HandlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        logging.warn("rest.server - loading private key from %s" % serverkey)
        ctx.use_privatekey_file (serverkey)
        logging.warn('rest.server - loading certificate from %s' % servercert)
        ctx.use_certificate_file(servercert)
        logging.warn('rest.server - loading chain of certifications from %s' % chain)
        ctx.set_verify_depth(2)
        ctx.load_client_ca(chain)
        #ctx.load_verify_locations(chain)
        logging.info('rest.server - creating SSL socket on %s' % str(server_address))
        callback = lambda conn,cert,errno,depth,retcode: retcode
        ctx.set_verify(SSL.VERIFY_FAIL_IF_NO_PEER_CERT | SSL.VERIFY_PEER, callback)
        ctx.set_session_id('jsonbot')
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                        self.socket_type))
        self.server_bind()  
        self.server_activate()

class SecureRequestHandler(RestRequestHandler):

    def setup(self):
        self.connection = self.request._sock
        self.request._sock.setblocking(1)
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.rbufsize)
