# gozerlib/admin.py
#
#

""" admin related data and functions. """

## gozerlib imports

from gozerlib.persist import Persist

## defines

plugin_packages = ['gozerlib.plugs', 'gozerlib.gae.plugs', 'commonplugs', 'myplugs', 'waveplugs', 'socketplugs']
default_plugins = ['gozerlib.plugs.admin', 'gozerlib.plugs.outputcache']

# these are set in gozerlib/boot.py

loaded = False
cmndtable = None 
pluginlist = None
callbacktable = None
