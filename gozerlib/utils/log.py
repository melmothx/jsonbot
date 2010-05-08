# gozerlio/utils/log.py
#
#

""" log module. """

## basic imports

import logging

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

def setloglevel(level_name):
    level = LEVELS.get(level_name, logging.NOTSET)
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    logging.basicConfig(level=level,
                    format='%(asctime)s - %(message)s - <%(funcName)s:%(lineno)s>')
    root.setLevel(level)
    logging.warn("loglevel is %s (%s)" % (str(level), level_name))
