# gozerlib/admin.py
#
#

""" admin related data and functions. """

## defines

try:
    import waveapi
    plugin_packages = ['gozerlib.plugs', 'gozerlib.gae.plugs', 'commonplugs', 'jsondir.myplugs', 'waveplugs']
except ImportError:
    plugin_packages = ['gozerlib.plugs', 'gozerlib.gae.plugs', 'commonplugs', 'jsondir.myplugs', 'waveplugs', 'socketplugs']

default_plugins = ['gozerlib.plugs.admin', 'gozerlib.plugs.outputcache']

# these are set in gozerlib/boot.py

loaded = False
cmndtable = None 
pluginlist = None
callbacktable = None
