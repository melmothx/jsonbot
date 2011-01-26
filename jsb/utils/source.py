# jsb/utils/source.py
#
#

""" get the location of a source """

## basic imports

import os
import logging

## getsource function

def getsource(mod):
    source = None
    splitted = mod.split(".")
    if len(splitted) == 1: splitted.append("")
    try:
        import pkg_resources
        source = pkg_resources.resource_filename(".".join(splitted[:len(splitted)-1]), splitted[-1])
    except ImportError:
        thedir = mod.replace(".", os.sep)
        if os.path.isdir(thedir): source = thedir
    #if not source and os.path.isdir("/home/jsb/.jsb"): source = "/home/jsb/.jsb" + os.sep + thedir
    if not source and os.path.isdir("/var/cache/jsb"): source = "/var/cache" + os.sep + thedir
    if not source and os.path.isdir("/usr/lib/jsb"): source = "/usr/lib" + os.sep + thedir
    if not source and os.path.isdir("/usr/jsb"): source = "/usr" + os.sep + thedir        
    logging.info("datadir - source is %s" % source)
    return source
