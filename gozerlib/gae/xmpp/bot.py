# gozerlib/xmpp/bot.py
#
#

""" XMPP bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.socklib.xmpp.presence import Presence

## google imports

from google.appengine.api import xmpp

## basic imports

import types
import logging

## classes

class XMPPBot(BotBase):

    """ XMPPBot just inherits from BotBase for now. """

    def __init__(self, cfg=None, users=None, plugs=None, jid="jsonbot@appspot.com", *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, jid, *args, **kwargs)
        self.jid = jid
        if self.cfg:
            self.cfg['type'] = 'xmpp'
        self.isgae = True
        self.type = "xmpp"

    def say(self, jids, body, from_jid=None, message_type=xmpp.MESSAGE_TYPE_CHAT, raw_xml=False, extend=0):
        """ output xmpp message. """
        if type(jids) == types.StringType:
            jids = [jids, ]

        logging.warn('xmpp - out - %s - %s' % (unicode(jids), unicode(body)))
        xmpp.send_message(jids, body, from_jid=from_jid, message_type=message_type, raw_xml=raw_xml)

    def saynocb(self, jids, body, from_jid=None, message_type=xmpp.MESSAGE_TYPE_CHAT, raw_xml=False, extend=0):
        """ output xmpp message. """
        if type(jids) == types.StringType:
            jids = [jids, ]

        logging.warn('xmpp - out - %s - %s' % (unicode(jids), unicode(body)))
        xmpp.send_message(jids, body, from_jid=from_jid, message_type=message_type, raw_xml=raw_xml)

    def invite(self, jid):
        xmpp.send_invite(jid)
