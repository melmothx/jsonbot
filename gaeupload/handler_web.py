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
boot()

## define

bot = WebBot(name='webbot')

## classes

class DispatchHandler(RequestHandler):

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

        event = WebEvent(bot=bot).parse(self.response, self.request)
        event.cbtype = "WEB"

        (userhost, user, u, nick) = checkuser(self.response, self.request, event)
        login = loginurl(self.response)
        logout = logouturl(self.response)

        if not user:
            start(self.response, {'appname': cfg['appname'] , 'plugins': getpluginlist() , 'who': 'login', 'loginurl': login, 'logouturl': logout, 'onload': 'consoleinit();'})
        else:
            start(self.response, {'appname': cfg['appname'] , 'plugins': getpluginlist() , 'who': userhost, 'loginurl': login, 'logouturl': logout, 'onload': 'consoleinit();'})

        try:
            bot.doevent(event)
            #self.response.out.write('</div>')
        except NoSuchCommand:
            self.response.out.write("sorry no %s command found." % event.usercmnd)
        except Exception, ex:
            handle_exception(event)

        #self.response.out.write('<br><div class="body"><i>"enter a command in the box above."</i><br></div>')
        #self.response.out.write('</div>')
        #closer(self.response)
        logging.warn("web_handler - out")

    def post(self):

        """ this is where the command get disaptched. """

        logging.debug("web - incoming - %s" % self.request.remote_addr)
        global starttime

        if starttime:
            self.response.starttime = starttime
            starttime = 0
        else:
            self.response.starttime = time.time()

        login = loginurl(self.response)
        logout = logouturl(self.response)

        event = WebEvent(bot=bot).parse(self.response, self.request)
        event.cbtype = "WEB"

        if not event.user:
            start(self.response, {'appname': cfg['appname'] , 'plugins': getpluginlist() , 'who': 'login', 'loginurl': login, 'logouturl': logout, 'onload': 'putFocus(0,0);'})
        else:
            start(self.response, {'appname': cfg['appname'] , 'plugins': getpluginlist() , 'who': event.userhost, 'loginurl': login, 'logouturl': logout, 'onload': 'putFocus(0,0);'})


        try:
            bot.doevent(event)
            #self.response.out.write('</div>')
        except NoSuchCommand:
            self.response.out.write("sorry no %s command found." % event.usercmnd)
        except Exception, ex:
            handle_exception(event)
               
        #closer(self.response)

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

application = WSGIApplication([('/', DispatchHandler),
                               ('/feeds', FeedListHandler),
                               ('/feeds/', FeedListHandler)],
                               debug=True)

## main

def main():
    global bot
    global application
    application.run()

if __name__ == "__main__":
    main()
