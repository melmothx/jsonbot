# gozerlib package
#
#

""" gozerlib core package. """

__version__ = "0.2"

__all__ = ['eventhandler', 'persistconfig', 'rest', 'jsbimport', 'admin', 'boot', 'botbase', 'callbacks', 'channelbase', 'commands', 'config', 'contrib', 'datadir', 'eggs', 'errors', 'eventbase', 'examples', 'fleet', 'gae', 'less', 'monitor', 'outputcache', 'periodical', 'persist', 'persiststate', 'plugins', 'plugs', 'runner', 'socklib', 'tasks', 'threadloop', 'threads', 'users', 'utils', 'console']

import os
import warnings

warnings.simplefilter('ignore')

from gozerlib.eggs import loadegg

try:
    from simplejson import loads
except ImportError:
    loadegg('simplejson', [os.getcwd(), ], log=True)
