# handler_docs.py
#
#

""" xmpp request handler. """

## jsb imports

from jsb.lib.version import getversion

## google imports

import webapp2

## basic imports

import sys
import time
import types
import logging

## greet

logging.warn(getversion('REDIRECT'))

## classes

class DocsHandler(webapp2.RequestHandler):

    def get(self, url=None):
        try:
            if not url.endswith(".html"):
                if not url.endswith('/'):
                    url += u"/index.html"
                else:
                    url += u"index.html"
            splitted = url.split('/')
            splitted.insert(2, 'html')
            goto = '/'.join(splitted)
            logging.warn("docs - redirecting %s" % goto)
            self.redirect(goto)
        except Exception, ex:
            handle_exception()
            #self.send_error(500)

application = webapp2.WSGIApplication([webapp2.Route(r'<url:.*>', DocsHandler)], 
                                      debug=True)

def main():
    global application
    application.run()

if __name__ == "__main__":
    main()
