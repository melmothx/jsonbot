# gozerlib/plugs/underauth.py
#
#

""" Handle non-ident connection on undernet. """

__copyright__ = 'this file is in the public domain'
__author__ = 'aafshar@gmail.com'

## gozerlib imports

from gozerlib.callbacks import callbacks

## basic imports

import logging

def pre_underauth_cb(bot, ievent):
    """ 
        Only respond to the message like:
        NOTICE AUTH :*** Your ident is disabled or broken, to continue
        to connect you must type /QUOTE PASS 16188.

    """
    args = ievent.arguments

    try:
        return (args[0] == u'AUTH' and
                args[-3] == u'/QUOTE' and
                args[-2] == u'PASS')
    except Exception, ex:
        return 0

def underauth_cb(bot, ievent):
    """
        Send the raw command to the server.

    """
    # last two elements of the arguments list are PASS <id>
    logging.debug("underauth - sending response")
    bot._raw(' '.join(ievent.arguments[-2:]))

callbacks.add('NOTICE', underauth_cb, pre_underauth_cb)
