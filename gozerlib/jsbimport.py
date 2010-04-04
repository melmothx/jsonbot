# gozerlib/jsbimport.py
#
#

""" use the imp module to import modules. """

import time
import sys
import imp
import os
import thread
import logging

def _import(name):
    mods = []
    mm = ""
    for m in name.split('.'):
        mm += m
        mods.append(mm)
        mm += "."

    for mod in mods:
        logging.debug("jsbimport - trying %s" % mod)
        imp = __import__(mod)

    logging.debug("jsbimport - got module %s" % sys.modules[name])
    return sys.modules[name]

def __import(name, path=None):

    """
        import module <name> with the imp module  .. will reload module is 
        already in sys.modules.

        :param name: name of the module to import (may contain dots)
        :type name: string
        :param path: optional path to search in
        :type path: string
        :rtype: module

    """

    logging.debug('import - importing %s' % name)

    splitted = name.split('.')
    
    for plug in splitted:
        fp, pathname, description = imp.find_module(plug, path)
        try:
           result = imp.load_module(plug, fp, pathname, description)
           try:
               path = result.__path__
           except:
               pass
        finally:
            if fp:
                fp.close()

    if result:
        return result

def force_import(name):

    """
        force import of module <name> by replacing it in sys.modules.

        :param name: name of module to import
        :type name: string
        :rtype: module

    """

    try:
        del sys.modules[name]
    except KeyError:
        pass
    plug = _import(name)
    return plug
