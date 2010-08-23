# gaeupload/handler_openid.py
#
#

""" Openid handler. """

## gozerlib imports

from gozerlib.gae.utils.web import loginurl
from gozerlib.config import cfg
from gozerlib.utils.generic import getversion

## google imports

from google.appengine.api import users
import webapp2 as webapp

## basic imports

import os
import logging
import urlparse
import urllib

## classes

class OpenIdLoginHandler(webapp.RequestHandler):

    def create_openid_url(self, continue_url):
        continue_url = urlparse.urljoin(self.request.url, continue_url)
        return "/_ah/login?continue=%s" % urllib.quote(continue_url)

    def get(self):
        cont = self.request.get('continue')
        logging.info('openid - login form %s' % cont)
        urlstring = u""
        for name, url in loginurl(self.request, self.response).iteritems():
            urlstring += '<a href="%s"><b>%s</b></a> - ' % (url, name)
        template_values = {
            'continue': cont,
            'urlstring': urlstring[:-3],
            'appname': getversion()
        }

        path = os.path.join(os.path.dirname(__file__), 'templates', 'login.html')
        from google.appengine.ext.webapp import template
        logging.info("openid - diplaying page to %s" % self.request.remote_addr)
        self.response.out.write(template.render(path, template_values))      

    def post(self):
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
