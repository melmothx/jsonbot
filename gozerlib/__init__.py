# gozerlib package
#
#

""" gozerlib core package. """

__version__ = "0.2"

__all__ = ['eventhandler', 'persistconfig', 'rest', 'jsbimport', 'admin', 'boot', 'botbase', 'callbacks', 'channelbase', 'commands', 'config', 'contrib', 'datadir', 'eggs', 'errors', 'eventbase', 'examples', 'fleet', 'gae', 'less', 'monitor', 'outputcache', 'periodical', 'persist', 'persiststate', 'plugins', 'plugs', 'runner', 'socklib', 'tasks', 'threadloop', 'threads', 'users', 'utils', 'console']

from gozerlib.eggs import loadegg

import os
import warnings

warnings.simplefilter('ignore')

loadegg('simplejson', [os.getcwd(), os.getcwd() + os.sep + 'jsbnest'], log=False)

