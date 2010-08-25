# handler_docs.py
#
#

""" xmpp request handler. """

## gozerlib imports

from gozerlib.utils.generic import getversion

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
        if not url.endswith(".html"):
            url += "/index.html"
        splitted = url.split('/')
        splitted.insert(2, 'html')
        goto = '/'.join(splitted)
        logging.warn("docs - redirecting %s" % goto)
        self.redirect(goto)

application = webapp2.WSGIApplication([webapp2.Route(r'<url:.*>', DocsHandler)], 
                                      debug=True)

def main():
    global application
    application.run()

if __name__ == "__main__":
    main()
