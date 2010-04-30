# gozerlio/utils/log.py
#
#

""" log module. """

import logging


import sys
import os

root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

basiclogger = root

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

def setloglevel(level_name):
    level = LEVELS.get(level_name, logging.NOTSET)
    #formatter = logging.Formatter("[%(asctime)s] (%(name)s) %(message)s")
    #logger = logging.getLogger('')
    #logger.propagate = True
    #stream = logging.StreamHandler()
    #stream.setFormatter(formatter)
    #stream.propagate = False
    basiclogger.setLevel(level)
    #logger.addHandler(stream)
    logging.info("loglevel is %s (%s)" % (str(level), level_name))
