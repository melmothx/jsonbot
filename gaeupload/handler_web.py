# handler_web.py
#
#

""" web request handler. """

import time
import logging

## gozerlib imports

from gozerlib.utils.generic import fromenc, toenc, getversion
from gozerlib.utils.xmpp import stripped
from gozerlib.plugins import plugs
from gozerlib.utils.exception import handle_exception
from gozerlib.persist import Persist
from gozerlib.errors import NoSuchCommand
from gozerlib.utils.log import setloglevel

## gaelib import

from gozerlib.gae.utils.auth import finduser
from gozerlib.gae.utils.web import start, closer, loginurl, logouturl, login

## google imports

from webapp2 import RequestHandler, Route, WSGIApplication
from google.appengine.ext.webapp import template

## simplejson import

from simplejson import loads

## basic imports

import sys
import time
import types
import os
import logging

## init

logging.info(getversion('GAE WEB'))

## classes

class HomePageHandler(RequestHandler):

    """ the bots web command dispatcher. """


    def options(self):
        self.response.headers.add_header("Allow: *")
        
    def get(self):

        """ show basic page. """
        logging.warn("web_handler - in")

        user = finduser()
        if not user:
            login(self.response, {'appname': 'JSONBOT' , 'who': 'not logged in yet', 'loginurl': 'not logged in', 'logouturl': 'JSONBOT', 'onload': 'consoleinit();'})
        else:
            logout = logouturl(self.request, self.response)
            start(self.response, {'appname': 'JSONBOT' , 'who': user, 'loginurl': 'logged in', 'logouturl': logout, 'onload': 'consoleinit();'})

        logging.warn("web_handler - out")
        
## the application 

application = WSGIApplication([('/', HomePageHandler)],
                               debug=True)

## main

def main():
    global application
    application.run()

if __name__ == "__main__":
    main()
