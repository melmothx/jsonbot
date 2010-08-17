# gaeupload/handler_openid.py
#
#

""" Openid handler. """

## gozerlib imports

from gozerlib.gae.utils.web import loginurl
from gozerlib.config import cfg

## google imports

from google.appengine.api import users
import webapp2 as webapp

## basic imports

import os

## classes

class OpenIdLoginHandler(webapp.RequestHandler):

    def get(self):
        continue_url = self.request.GET.get('continue')
        openid_url = self.request.GET.get('openid')
        if not openid_url:
            from google.appengine.ext.webapp import template
            urlstring = u""
            for name, url in loginurl(self.request, self.response).iteritems():
                urlstring += '<a href="%s"><b>%s</b></a> - ' % (url, name)

            path = os.path.join(os.path.dirname(__file__), 'templates', 'login.html')
            self.response.out.write(template.render(path, {'continue': continue_url, 'appname': cfg['appname'], 'urlstring': urlstring[:-3]}))
        else:
            try:
                if not continue_url:
                    self.redirect(users.create_login_url(continue_url, None, openid_url))
                else:
                    self.redirect(users.create_login_url("/", None, openid_url))
            except TypeError:
                self.redirect(users.create_login_url("/", None, openid_url))
         
## the application 

application = webapp.WSGIApplication([('/_ah/login_required', OpenIdLoginHandler),
                               ('/_ah/login', OpenIdLoginHandler)],
                               debug=True)

## main

def main():
    global application
    application.run()

if __name__ == "__main__":
    main()

