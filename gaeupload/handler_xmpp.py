# handler_xmpp.py
#
#

""" xmpp request handler. """

## gozerlib imports

from gozerlib.utils.generic import fromenc, toenc, getversion
from gozerlib.utils.lazydict import LazyDict
from gozerlib.utils.exception import handle_exception
from gozerlib.plugins import plugs
from gozerlib.boot import boot, plugin_packages
from gozerlib.remote.event import RemoteEvent
from gozerlib.remote.bot import RemoteBot

## gaelib imports

from gozerlib.gae.xmpp.bot import XMPPBot
from gozerlib.gae.xmpp.event import XMPPEvent
from gozerlib.gae.utils.auth import checkuser

## google imports

from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users as gusers
from google.appengine.ext import db
from google.appengine.ext.webapp import xmpp_handlers

from simplejson import loads

import wsgiref.handlers
import sys
import time
import types
import logging

logging.info(getversion('GAE XMPP'))

boot()

## defines

bot = XMPPBot()

## functions

def xmppbox(response):
    response.out.write("""
          <form action="/_ah/xmpp/message/chat/" method="post">
            <div><b>enter command:</b> <input type="commit" name="body">
          </form>
          """)

## classes

class XMPPHandler(webapp.RequestHandler):

    """ relay incoming messages to the bot. """

    def post(self):
        try:
            logging.info("XMPP incoming: %s" % self.request.remote_addr)

            if not self.request.POST.has_key('from'):
                logging.debug('no from in POST: %s' % str(self.request.POST))
                return

            if not self.request.POST.has_key('to'):
                logging.debug('no to in POST: %s' % str(self.request.POST))
                return

            event = XMPPEvent(bot=bot).parse(self.request, self.response)
            bot.doevent(event)

        except Exception, ex:
            handle_exception()
            self.send_error(500)

application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/', XMPPHandler), ],
                                      debug=True)

def main():
    global application
    global bot
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
