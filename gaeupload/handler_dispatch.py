# handler_dispatch.py
#
#

""" jsonbot dispatch handler.  dispatches remote commands.  """

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
from gozerlib.commands import public
from gozerlib.gae.utils.web import loginurl

## gaelib imports

from gozerlib.gae.web.bot import WebBot
from gozerlib.gae.web.event import WebEvent
from gozerlib.gae.utils.auth import checkuser

## google imports

from webapp2 import RequestHandler, Route, WSGIApplication
from google.appengine.ext.webapp import template
from google.appengine.api import users as gusers

## simplejson import

from simplejson import loads

## basic imports

import sys
import time
import types
import os
import logging

logging.warn(getversion('DISPATCH'))
boot()

bot = WebBot()

class Dispatch_Handler(RequestHandler):

    """ the bots remote command dispatcher. """

    def options(self):
         self.response.headers.add_header('Content-Type', 'application/x-www-form-urlencoded')
         #self.response.headers.add_header("Cache-Control", "private")
         self.response.headers.add_header("Server", getversion())
         self.response.headers.add_header("Public", "*")
         self.response.headers.add_header('Accept', '*')
         self.response.headers.add_header('Access-Control-Allow-Origin', self.request.headers['Origin'])
         self.response.out.write("Allow: *")
         self.response.out.write('Access-Control-Allow-Origin: *') 
         logging.warn("dispatch - options response send to %s - %s" % (self.request.remote_addr, str(self.request.headers)))

    def post(self):

        """ this is where the command get disaptched. """

        try:
            logging.warn("DISPATCH incoming: %s - %s" % (self.request.get('content'), self.request.remote_addr))
            if not gusers.get_current_user():
                logging.warn("denied access for %s - %s" % (self.request.remote_addr, self.request.get('content')))
                self.response.set_status(400)
                return
            #logging.debug(str(self.request))
            event = WebEvent(bot=bot).parse(self.response, self.request)
            event.cbtype = "DISPATCH"
            event.type = "DISPATCH"
            event.finish()
            #(userhost, user, u, nick) = checkuser(self.response, self.request, event)
            #logging.("launching event: %s" % event.dump())
            bot.doevent(event)

        except NoSuchCommand:
            event.reply("no such command: %s" % event.usercmnd)
        except Exception, ex:
            handle_exception()
            self.send_error(500)

    get = post

# the application 

application = WSGIApplication([Route('/dispatch/', Dispatch_Handler) ], debug=True)

def main():
    global bot
    global application
    application.run()

if __name__ == "__main__":
    main()
