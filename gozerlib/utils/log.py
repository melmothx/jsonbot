# gozerlio/utils/log.py
#
#

""" log module. """

import logging
import sys

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

def setloglevel(level_name):
    level = LEVELS.get(level_name, logging.NOTSET)
    logging.warn("setting loglevel to %s (%s)" % (str(level), level_name))
    logger = logging.getLogger()
    logger.setLevel(level)

