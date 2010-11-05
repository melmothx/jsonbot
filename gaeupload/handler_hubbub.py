# handler_hubbub.py
#
#

## gozerlib imports

from gozerlib.contrib import feedparser
from gozerlib.version import getversion
from gozerlib.plugins import plugs

## google imports

from google.appengine.api import urlfetch
from google.appengine.api import xmpp
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import xmpp_handlers

## basic imports

import base64
import logging
import urllib
import urlparse
import uuid

logging.warn(getversion('GAE HUBBUB'))

if not plugs.has_key("commonplugs.hubbub"):
    p = plugs.load("commonplugs.hubbub")
else:
    p = plugs["commonplugs.hubbub"]

class CallbackHandler(webapp.RequestHandler):

  def get(self):
    logging.warn('hubbub - incoming GET')
    if self.request.GET['hub.mode'] == 'unsubscribe':
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write(self.request.GET['hub.challenge'])
      return
      
    if self.request.GET['hub.mode'] != 'subscribe':
      self.error(400)
      return

    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(self.request.GET['hub.challenge'])

  def post(self):

    """Handles new content notifications."""

    logging.warn("hubbub - incoming POST")

    try:
        p.watcher.incoming(self.request.body)
    except IndexError:
        logging.error("hubbub plugin did not load properly")
    except Exception, ex:
        handle_exception()
        self.send_error(500)

application = webapp.WSGIApplication([('/(?:hubbub)', CallbackHandler)], debug=False)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
