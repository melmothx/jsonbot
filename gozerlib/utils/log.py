# gozerlio/utils/log.py
#
#

""" log module. """

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
                    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)s - %(message)s')
                    #format='%(asctime)s - %(message)s')
    #formatter = logging.Formatter("[%(asctime)s] (%(name)s) %(message)s")
    #logger = logging.getLogger('')
    #logger.propagate = True
    #stream = logging.StreamHandler()
    #stream.setFormatter(formatter)
    #stream.propagate = False
    root.setLevel(level)
    #logger.addHandler(stream)
    logging.warn("loglevel is %s (%s)" % (str(level), level_name))
