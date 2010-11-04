# gaeupload/handler_openid.py
#
#

""" Openid handler. """

## gozerlib imports

from gozerlib.gae.utils.web import loginurl
from gozerlib.version import getversion
from gozerlib.utils.exception import handle_exception

## google imports

from google.appengine.api import users
import webapp2 as webapp

## basic imports

import os
import logging
import urlparse
import urllib
import warnings
import socket

## classes

class OpenIdLoginHandler(webapp.RequestHandler):

    def create_openid_url(self, continue_url):
        continue_url = urlparse.urljoin(self.request.url, continue_url)
        return "/_ah/login?continue=%s" % urllib.quote(continue_url)

    def get(self):
        try:
            cont = self.request.get('continue')
            logging.info('openid - login form %s' % cont)
            urlstring = self.create_openid_url(cont)
            template_values = {
                'continue': cont,
                'urlstring': urlstring,
                'appname': getversion()
            }
            try: host = socket.gethostname()
            except AttributeError:
                if os.environ.get('HTTP_HOST'): host = os.environ['HTTP_HOST']
                else: host = os.environ['SERVER_NAME']
            inputdict = {'version': getversion(), 'host': host}
            template_values.update(inputdict)
            temp = os.path.join(os.getcwd(), 'templates/login.html')
            from google.appengine.ext.webapp import template
            outstr = template.render(temp, template_values)  
            self.response.out.write(outstr)
        except Exception, ex:
            handle_exception()

    def post(self):
        try:
            cont = self.request.get('continue')
            conturl = self.create_openid_url(cont)
            logging.info('openid - %s' % cont)
            openid = self.request.get('openid_identifier')
            if openid:
                login_url = users.create_login_url(cont, None, openid)
                logging.info('openid - redirecting to url %s (%s)' % (login_url, openid))
                self.redirect(login_url)
            else:
                logging.warn("denied access for %s - %s - %s" % (self.request.remote_addr, cont, openid))
                self.send_error(400)
        except Exception, ex:
            handle_exception()

## the application 

application = webapp.WSGIApplication([
                               ('/_ah/login_required', OpenIdLoginHandler)],
                               debug=True)

## main

def main():
    global application
    application.run()

if __name__ == "__main__":
    main()
