# gozerlib/errors.py
#
#

""" gozerbot exceptions. """

from gozerlib.utils.trace import calledfrom
import sys

class FeedProviderError(Exception):
    pass

class CantSaveConfig(FeedProviderError):
    pass

class NoOwnerSet(FeedProviderError):
    pass

class NoSuchUser(FeedProviderError):
    pass

class NoSuchBotType(FeedProviderError):
    pass

class NoSuchWave(FeedProviderError):
    pass

class NoSuchCommand(FeedProviderError):
    pass

class NoSuchPlugin(FeedProviderError):
    pass

class NoOwnerSet(FeedProviderError):
    pass

class PlugsNotConnected(FeedProviderError):
    pass
