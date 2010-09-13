# handler_remote.py
#
#

""" JSONBOT Remote Events Network. """

import time

starttime = time.time()

## gozerlib imports

from gozerlib.remote.bot import RemoteBot
from gozerlib.remote.event import RemoteEvent
from gozerlib.utils.generic import fromenc, toenc, getversion
from gozerlib.utils.xmpp import stripped
from gozerlib.plugins import plugs
from gozerlib.persist import Persist
from gozerlib.utils.exception import handle_exception
from gozerlib.boot import boot

## google imports

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users as gusers

## simplejson import

from simplejson import loads

## basic imports

import wsgiref.handlers
import sys
import time
import types
import os
import logging

logging.info(getversion('REMOTE'))

#boot()
bot = RemoteBot()
#plugs.loadall()

class EventNetHandler(webapp.RequestHandler):

    """ the bots remote event dispatcher. """

    def post(self):

        """ this is where the command get disaptched. """

        logging.debug("REMOTE incoming: %s" % self.request.remote_addr)
        event = RemoteEvent()
        event.parse(self.response, self.request)
        event.bot = bot
        event.title = event.channel

        try:
            event.bot.doevent(event)

        except Exception, ex:
            handle_exception()
            self.send_error(500)

    get = post

# the application 

application = webapp.WSGIApplication([('/remote', EventNetHandler),
                                      ('/remote/', EventNetHandler)],
                                      debug=True)

def main():
    global bot
    global application
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
