# gozerlib/admin.py
#
#

""" admin related data and functions. """

## gozerlib imports

from gozerlib.persist import Persist

## defines

plugin_packages = ['gozerlib.plugs', 'commonplugs', 'myplugs', 'waveplugs', 'socketplugs']
default_plugins = ['gozerlib.plugs.admin', ]

loaded = False
cmndtable = None 
pluginlist = None
callbacktable = None
