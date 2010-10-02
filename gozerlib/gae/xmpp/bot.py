# gozerlib/gae/xmpp/bot.py
#
#

""" XMPP bot. """

## gozerlib imports

from gozerlib.botbase import BotBase
from gozerlib.socklib.xmpp.presence import Presence
from gozerlib.utils.generic import strippedtxt

## basic imports

import types
import logging

## XMPPBot class

class XMPPBot(BotBase):

    """ XMPPBot just inherits from BotBase for now. """

    def __init__(self, cfg=None, users=None, plugs=None, botname="gae-xmpp", *args, **kwargs):
        BotBase.__init__(self, cfg, users, plugs, botname, *args, **kwargs)
        self.jid = "jsonbot@appspot.com"
        if self.cfg: self.cfg['type'] = 'xmpp'
        self.isgae = True
        self.type = "xmpp"

    def out(self, jids, txt, how="msg", event=None, origin=None, groupchat=None, *args, **kwargs):
        """ output xmpp message. """
        if type(jids) != types.ListType: jids = [jids, ]
        logging.warn("%s - OUT - %s" % (self.name, jids))
        self.outnocb(jids, txt)
        for jid in jids:
            self.outmonitor(self.nick, jid, txt)

    def outnocb(self, jids, txt, from_jid=None, message_type=None, raw_xml=False, event=None, origin=None, groupchat=None, *args, **kwargs):
        """ output xmpp message. """
        from google.appengine.api import xmpp
        if not message_type: message_type = xmpp.MESSAGE_TYPE_CHAT
        if type(jids) != types.ListType: jids = [jids, ]
        txt = self.normalize(txt)
        logging.debug(u"%s - xmpp - out - %s" % (self.name, txt))             
        xmpp.send_message(jids, txt, from_jid=from_jid, message_type=message_type, raw_xml=raw_xml)

    def invite(self, jid):
        """ send an invite to another jabber user. """
        from google.appengine.api import xmpp
        xmpp.send_invite(jid)

    def normalize(self, what):
        """ remove markup code as its not yet supported by our GAE XMPP bot. """
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
