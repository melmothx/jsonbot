# handler_gadgetexec.py
#
#

""" jsonbot exec handler.  just return the results in a <div>. """

## gozerlib imports

from gozerlib.utils.generic import fromenc, toenc, getversion
from gozerlib.utils.xmpp import stripped
from gozerlib.utils.url import getpostdata, useragent
from gozerlib.plugins import plugs
from gozerlib.persist import Persist
from gozerlib.utils.exception import handle_exception
from gozerlib.boot import boot
from gozerlib.fleet import fleet
from gozerlib.config import cfg as maincfg
from gozerlib.errors import NoSuchCommand

## gaelib imports

from gozerlib.gae.wave.bot import WaveBot
from gozerlib.gae.web.bot import WebBot
from gozerlib.gae.web.event import WebEvent
from gozerlib.gae.utils.web import execbox, commandbox, closer

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

logging.warn(getversion('GADGETEXEC'))

bot = WebBot()

class HB_Handler(webapp.RequestHandler):

    """ the bots exec command dispatcher. """

    def options(self):
         logging.warn(dir(self.request))
         #logging.warn(self.request)
         logging.warn(dir(self.response))
         #self.response.headers.add_header('Content-Type', 'application/x-www-form-urlencoded')
         #self.response.headers.add_header("Cache-Control", "private")
         self.response.headers.add_header("Server", getversion())
         self.response.headers.add_header("Public", "*")
         self.response.headers.add_header('Accept', '*')
         self.response.headers.add_header('Access-Control-Allow-Origin', self.request.headers['Origin'])
         #self.response.headers.add_header('Access-Control-Allow-Origin', '*') 
         #self.response.headers.add_header('Content-Length', '0') 
         self.response.out.write("Allow: *")
         self.response.out.write('Access-Control-Allow-Origin: *') 
         logging.warn("gadgetexec - optins response send to %s - %s" % (self.request.remote_addr, str(self.request.headers)))

    def post(self):

        """ this is where the command get disaptched. """

        try:
            logging.debug("EXEC incoming: %s" % self.request.remote_addr)
            #logging.debug(str(self.request))
            event = WebEvent(bot=bot).parse(self.response, self.request)
            #logging.debug(dir(self.request))
            #logging.debug(self.request.params)
            event.type = "GADGET"
            logging.debug(event.dump())
            self.response.headers.add_header('Access-Control-Allow-Origin', '*')

            try:
                bot.doevent(event)
            except NoSuchCommand:
                event.reply("no %s command found" % event.usercmnd)

        except Exception, ex:
            handle_exception()

    get = post

# the application 

application = webapp.WSGIApplication([('/gadgetexec', HB_Handler),
                                      ('/gadgetexec/', HB_Handler)],
                                      debug=True)

def main():
    global webbot
    global application
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
