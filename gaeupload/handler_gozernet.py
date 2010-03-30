# handler_gozernet.py
#
#

""" gozernet handler. handlers incoming events (json). """

import time

starttime = time.time()

## gozerlib imports

from gozerlib.gozernet.bot import GozerNetBot
from gozerlib.gozernet.event import RemoteEvent
from gozerlib.utils.generic import fromenc, toenc, getversion
from gozerlib.utils.xmpp import stripped
from gozerlib.plugins import plugs
from gozerlib.utils.auth import checkuser
from gozerlib.persist import Persist
from gozerlib.utils.exception import handle_exception
from gozerlib.boot import boot

## google imports

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users as gusers

## simplejson import

from waveapi.simplejson import loads

## basic imports

import wsgiref.handlers
import sys
import time
import types
import os
import logging

logging.warn(getversion('GOZERNET'))

boot()
bot = GozerNetBot('gozernet')
plugs.loadall()

class GozerNetHandler(webapp.RequestHandler):

    """ gozernet request handler. """

    def post(self):

        """ this is where the command get disaptched. """

        (userhost, user, u, nick) = checkuser(self.response, self.request)
        logging.debug("GOZERNET incoming: %s" % self.request.remote_addr)
        event = RemoteEvent()
        event.parse(self.response, self.request)
        event.bot = bot
        event.title = event.channel

        try:
            event.bot.doevent(event)

        except Exception, ex:
            handle_exception(event)

    get = post

# the application 

application = webapp.WSGIApplication([('/gozernet', EventNetHandler),
                                      ('/gozernet/', EventNetHandler)],
                                      debug=True)

def main():
    global bot
    global application
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
