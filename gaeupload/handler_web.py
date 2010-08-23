# handler_web.py
#
#

""" web request handler. """

import time
import logging

starttime = time.time()
#logging.debug('start time: %s' % time.ctime(time.time()))

## gozerlib imports

from gozerlib.utils.generic import fromenc, toenc, getversion
from gozerlib.utils.xmpp import stripped
from gozerlib.plugins import plugs
from gozerlib.config import cfg 
from gozerlib.utils.exception import handle_exception
from gozerlib.boot import boot, getcmndtable, getpluginlist
from gozerlib.persist import Persist
from gozerlib.errors import NoSuchCommand
from gozerlib.utils.log import setloglevel
from gozerlib.commands import public

## gaelib import

from gozerlib.gae.web.bot import WebBot
from gozerlib.gae.web.event import WebEvent
from gozerlib.gae.utils.auth import checkuser
from gozerlib.gae.utils.web import commandbox, start, closer, loginurl, logouturl

## google imports

from webapp2 import RequestHandler, Route, WSGIApplication
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
        global starttime

        if starttime:
            self.response.starttime = starttime
            starttime = 0
        else:
            self.response.starttime = time.time()

        if True:
            urlstring = u""
            for name, url in loginurl(self.request, self.response).iteritems():
                urlstring += '<a href="%s"><b>%s</b></a> - ' % (url, name)

            (userhost, user, u, nick) = checkuser(self.response, self.request)
            if not user:
                path = os.path.join(os.path.dirname(__file__), 'templates', 'login.html')
                self.response.out.write(template.render(path, {'appname': getversion(), 'urlstring': urlstring[:-3]}))
                return

            login = "logged in"
            logout = logouturl(self.request, self.response)

            if not user:
                login(self.response, {'appname': cfg['appname'] , 'plugins': getpluginlist() , 'who': 'not logged in yet', 'loginurl': login, 'logouturl': logout, 'onload': 'consoleinit();', 'urlstring': urlstring[:-3]})
            else:
                start(self.response, {'appname': cfg['appname'] , 'plugins': getpluginlist() , 'who': userhost, 'loginurl': login, 'logouturl': logout, 'onload': 'consoleinit();', 'urlstring': urlstring[:-3]})

        logging.warn("web_handler - out")
        
class FeedListHandler(RequestHandler):

    """ the bots web command dispatcher. """


    def get(self):

        """ show basic page. """
        global starttime
        from waveplugs.hubbub import HubbubWatcher
        watcher = HubbubWatcher('hubbub')
        feeds = watcher.getall()

        for feed in feeds.values():

            self.response.out.write("%s %s<br>\n" % (feed.data.name, feed.data.url))

## the application 

application = WSGIApplication([('/', HomePageHandler)],
                               debug=True)

## main

def main():
    global bot
    global application
    application.run()

if __name__ == "__main__":
    main()
