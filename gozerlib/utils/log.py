# gozerlib/utils/log.py
#
#

""" log module. """

## basic imports

import logging

## defines

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'warn': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

## setloglevel function

def setloglevel(level_name):
    """ set loglevel to level_name. """
    level = LEVELS.get(level_name, logging.NOTSET)
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers: root.removeHandler(handler)
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s - <%(funcName)s:%(lineno)s>')
    root.setLevel(level)
    logging.info("loglevel is %s (%s)" % (str(level), level_name))
