# handler_task.py
#
#

""" jsonbot task handler. """

## gozerlib imports

from gozerlib.plugins import plugs
from gozerlib.version import getversion
from gozerlib.utils.exception import handle_exception
from gozerlib.tasks import taskmanager

## google imports

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

## simplejson import

from waveapi.simplejson import loads

## basic imports

import wsgiref.handlers
import logging

## vars

periodicals =  ['commonplugs.rss', 'gozerlib.plugs.botevent']
mountpoints = ['rss', 'botevent']

##

logging.info(getversion('TASK'))

for plugin in periodicals:
    plugs.reload(plugin)


class TaskHandler(webapp.RequestHandler):

    """ the bots task handler. """

    def get(self):
        try:
            """ this is where the task gets dispatched. """
            path = self.request.path
            if path.endswith('/'):
                path = path[:-1]
            taskname = path.split('/')[-1].strip()
            logging.debug("using taskname: %s" % taskname)

            inputdict = {}
            for name, value in self.request.environ.iteritems():
                if not 'wsgi' in name:
                    inputdict[name] = value

            taskmanager.dispatch(taskname, inputdict, self.request, self.response)

        except Exception, ex:
            handle_exception()
            #self.send_error(500)

    def post(self):
        """ this is where the task gets dispatched. """
        try:
            path = self.request.path
            if path.endswith('/'):
                path = path[:-1]
            taskname = path.split('/')[-1].strip()
            logging.debug("using taskname: %s taken from %s" % (taskname, path))
            if not taskname:
                return

            inputdict = {}
            for name, value in self.request.environ.iteritems():
                if not 'wsgi' in name:
                    inputdict[name] = value

            taskmanager.dispatch(taskname, inputdict, self.request, self.response)

        except Exception, ex:
            handle_exception()
            #self.send_error(500)

# the application 

mountlist = []

for mount in mountpoints:
    mountlist.append(('/tasks/%s' % mount, TaskHandler))

application = webapp.WSGIApplication(mountlist, debug=True)

def main():
    global application
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
