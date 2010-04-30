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
    logger = logging.getLogger()
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s] (%(levelname)s) %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logging.info("loglevel is %s (%s)" % (str(level), level_name))
