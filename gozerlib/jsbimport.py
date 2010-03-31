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

def _import(name, path=None):

    """
        import module <name> with the imp module  .. will reload module is 
        already in sys.modules.

        :param name: name of the module to import (may contain dots)
        :type name: string
        :param path: optional path to search in
        :type path: string
        :rtype: module

        .. literalinclude:: ../../gozerbot/gozerimport.py
            :pyobject: gozer_import

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

        .. literalinclude:: ../../gozerbot/gozerimport.py
            :pyobject: force_import

    """

    try:
        del sys.modules[name]
    except KeyError:
        pass
    plug = _import(name)
    if plug:
        sys.modules[name] = plug
        return plug
