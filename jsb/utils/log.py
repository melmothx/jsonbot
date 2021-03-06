# jsb/utils/log.py
#
#

""" log module. """

## basic imports

import logging
import logging.handlers
import os
import os.path
import getpass

## defines

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'warn': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

try:
    import waveapi
except ImportError:
    if os.path.isdir('/var/log/jsb') and getpass.getuser() == "jsb": LOGDIR = "/var/log/jsb"
    else: LOGDIR = os.path.expanduser("~") + os.sep + ".jsb" + os.sep + "botlogs"

try:
    ddir = os.sep.join(LOGDIR.split(os.sep)[:-1])
    if not os.path.isdir(ddir): os.mkdir(ddir)
except: pass

try:
    if not os.path.isdir(LOGDIR): os.mkdir(LOGDIR)
except: pass

format = "%(asctime)s - %(message)s - <%(threadName)s+%(module)s-%(funcName)s:%(lineno)s>"

try:
    import waveapi
except ImportError:
    try:
        filehandler = logging.handlers.TimedRotatingFileHandler(LOGDIR + os.sep + "jsb.log", 'midnight')
        formatter = logging.Formatter(format)
        filehandler.setFormatter(formatter)  
    except IOError:
        filehandler = None

## setloglevel function

def setloglevel(level_name):
    """ set loglevel to level_name. """
    if not level_name: return
    level = LEVELS.get(level_name.lower(), logging.NOTSET)
    root = logging.getLogger("")
    if root.handlers:
        for handler in root.handlers: root.removeHandler(handler)
    logging.basicConfig(level=level, format=format)
    try: import waveapi
    except ImportError:
        if filehandler: root.addHandler(filehandler)
    root.setLevel(level)
    logging.warn("loglevel is %s (%s)" % (str(level), level_name))
