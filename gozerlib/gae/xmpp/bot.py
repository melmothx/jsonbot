# gozerlib/gae/xmpp/bot.py
#
#

""" XMPP bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.socklib.xmpp.presence import Presence

## basic imports

import types
import logging

## classes

class XMPPBot(BotBase):

    """ XMPPBot just inherits from BotBase for now. """

    def __init__(self, cfg=None, users=None, plugs=None, botname="gae-xmpp", *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, botname, *args, **kwargs)
        self.jid = "jsonbot@appspot.com"
        if self.cfg:
            self.cfg['type'] = 'xmpp'
        self.isgae = True
        self.type = "xmpp"

    def say(self, jids, body, from_jid=None, message_type=None, raw_xml=False, extend=0, *args, **kwargs):
        """ output xmpp message. """
        from google.appengine.api import xmpp
        if not message_type: message_type = xmpp.MESSAGE_TYPE_CHAT
        if type(jids) == types.StringType: jids = [jids, ]
        xmpp.send_message(jids, body, from_jid=from_jid, message_type=message_type, raw_xml=raw_xml, *args, **kwargs)
        for jid in jids:
            self.outmonitor(self.nick, jid, body)

    def saynocb(self, jids, body, from_jid=None, message_type=None, raw_xml=False, extend=0):
        """ output xmpp message. """
        from google.appengine.api import xmpp
        if not message_type: message_type = xmpp.MESSAGE_TYPE_CHAT
        if type(jids) == types.StringType: jids = [jids, ]
        xmpp.send_message(jids, body, from_jid=from_jid, message_type=message_type, raw_xml=raw_xml)

    def out(self, printto, txt, how="msg", event=None, origin=None, groupchat=None, *args, **kwargs):
        self.say(printto, txt)

    def outnocb(self, printto, txt, event=None, origin=None, groupchat=None, *args, **kwargs):
        self.saynocb(printto, txt)

    def invite(self, jid):
        from google.appengine.api import xmpp
        xmpp.send_invite(jid)

    def normalize(self, what):
        #what = re.sub("\s+", " ", unicode(what))
        what = strippedtxt(unicode(what))
        what = what.replace("<b>", "")
        what = what.replace("</b>", "")
        what = what.replace("&lt;b&gt;", "")
        what = what.replace("&lt;/b&gt;", "")
        what = what.replace("<i>", "")
        what = what.replace("</i>", "")
        what = what.replace("&lt;i&gt;", "")
        what = what.replace("&lt;/i&gt;", "")
        return what
