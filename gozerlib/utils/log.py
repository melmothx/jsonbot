# gozerlib/utils/log.py
#
#

""" log module. """

## basic imports

import logging
import logging.handlers
import os
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
    if getpass.getuser() == "jsonbot": LOGDIR = "/var/log/jsonbot"
    else: LOGDIR = os.path.expanduser("~") + os.sep + ".jsonbot" + os.sep + "botlogs"

try:
    ddir = os.sep.join(LOGDIR.split(os.sep)[:-1])
    if not os.path.isdir(ddir): os,.mkdir(ddir)
except: pass

try:
    if not os.path.isdir(LOGDIR): os.mkdir(LOGDIR)
except: pass

format = "%(asctime)s - %(levelname)s - %(message)s - <%(threadName)s+%(module)s-%(funcName)s:%(lineno)s>"

try:
    import waveapi
except ImportError:
    filehandler = logging.handlers.TimedRotatingFileHandler(LOGDIR + os.sep + "jsonbot.log", 'midnight')
    formatter = logging.Formatter(format)
    filehandler.setFormatter(formatter)  

## setloglevel function

def setloglevel(level_name):
    """ set loglevel to level_name. """
    level = LEVELS.get(level_name, logging.NOTSET)
    root = logging.getLogger("")
    if root.handlers:
        for handler in root.handlers: root.removeHandler(handler)
    logging.basicConfig(level=level, format=format)
    try: import waveapi
    except ImportError: root.addHandler(filehandler)
    root.setLevel(level)
    logging.info("loglevel is %s (%s)" % (str(level), level_name))
