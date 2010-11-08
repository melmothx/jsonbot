# gozerlib/wave/bot.py
#
#

""" google wave bot. """

## gozerlib imports

from gozerlib.persist import Persist
from gozerlib.botbase import BotBase
from gozerlib.plugins import plugs
from gozerlib.version import getversion
from gozerlib.callbacks import callbacks
from gozerlib.outputcache import add
from gozerlib.config import Config
from gozerlib.utils.locking import lockdec
from gozerlib.utils.exception import handle_exception
from gozerlib.jsbimport import _import_byfile
from gozerlib.datadir import getdatadir()

## gaelib imports

from gozerlib.gae.utils.auth import finduser
from event import WaveEvent
from waves import Wave

## waveapi v2 imports

from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import ops
from waveapi import blip
from waveapi import appengine_robot_runner

import waveapi

## generic imports

import logging
import cgi
import os
import time
import thread
import simplejson

## credentials

import gozerdata.config.credentials as credentials

## defines

saylock = thread.allocate_lock()
saylocked = lockdec(saylock)

## WaveBot claass

class WaveBot(BotBase, robot.Robot):

    """ bot to implement google wave stuff. """

    def __init__(self, cfg=None, users=None, plugs=None, name="gae-wave", domain=None,
                 image_url='http://jsonbot.appspot.com/assets/favicon.png',
                 profile_url='http://jsonbot.appspot.com/', *args, **kwargs):
        sname = 'jsonbot'
        BotBase.__init__(self, cfg, users, plugs, name, *args, **kwargs)
        if cfg: self.domain = cfg['domain'] or 'googlewave.com'
        else: self.domain = domain or 'googlewave.com'
        if self.cfg and self.cfg['domain'] != self.domain:
            self.cfg['domain'] = self.domain
            self.cfg.save()
        self.type = 'wave'
        self.nick = name or sname
        robot.Robot.__init__(self, name=sname, image_url=image_url, profile_url=profile_url)
        _import_byfile("credentials", getdatadir() + os.sep + "config" + os.sep + "credentials.py")
        self.set_verification_token_info(credentials.verification_token[self.domain], credentials.verification_secret[self.domain])
        self.setup_oauth(credentials.Consumer_Key[self.domain], credentials.Consumer_Secret[self.domain],
                             server_rpc_base=credentials.RPC_BASE[self.domain])
        self.register_handler(events.BlipSubmitted, self.OnBlipSubmitted)
        self.register_handler(events.WaveletSelfAdded, self.OnSelfAdded)
        self.register_handler(events.WaveletParticipantsChanged, self.OnParticipantsChanged)
        self.iswave = True
        self.isgae = True
 
    def OnParticipantsChanged(self, event, wavelet):
        """ invoked when any participants have been added/removed. """
        wevent = WaveEvent()
        wevent.parse(self, event, wavelet)
        wevent.bind(self)
        whitelist = wevent.chan.data.whitelist
        if not whitelist: whitelist = wevent.chan.data.whitelist = []
        participants = event.participants_added
        logging.warning("wave - %s - %s joined" % (wevent.chan.data.title, participants))
        if wevent.chan.data.protected:
            for target in participants:
                if target not in whitelist and target != 'jsonbot@appspot.com' and target != wevent.chan.data.owner:
                    logging.warn("wave - %s - setting %s to read-only" % (wevent.chan.data.title, target))
                    wevent.root.participants.set_role(target, waveapi.wavelet.Participants.ROLE_READ_ONLY)
        callbacks.check(self, wevent)

    def OnSelfAdded(self, event, wavelet):
        """ invoked when the robot has been added. """
        logging.warn('wave - joined "%s" (%s) wave' % (wavelet._wave_id, wavelet._title))
        wevent = WaveEvent()
        wevent.parse(self, event, wavelet)
        wevent.bind(self)
        logging.debug("wave - owner is %s" % wevent.chan.data.owner)
        wevent.chan.data.json_data = wavelet.serialize()
        wevent.chan.save()
        wevent.reply("Welcome to %s (see !help) or http://jsonbot.appspot.com/docs/html/index.html" % getversion())
        callbacks.check(self, wevent)

    def OnBlipSubmitted(self, event, wavelet):
        """ new blip added. here is where the command dispatching takes place. """
        wevent = WaveEvent()
        wevent.parse(self, event, wavelet)
        wevent.bind(self)
        wevent.auth = wevent.userhost
        wave = wevent.chan
        wave.data.seenblips += 1
        wave.data.lastedited = time.time()
        self.doevent(wevent)

    def _raw(self, txt, event=None, *args, **kwargs):
        """ output some txt to the wave. """
        assert event.chan
        if not event.chan: logging.error("%s - event.chan is not set" % self.name) ; return
        if event.chan.data.json_data: wavelet = self.blind_wavelet(event.chan.data.json_data)
        else: logging.info("did not join channel %s" % event.id) ; return
        if not wavelet: logging.error("cant get wavelet") ; return
        txt = self.normalize(txt)
        txt = unicode(txt.strip())
        logging.debug("%s - wave - out - %s" % (self.name, txt))             
        try:
            annotations = []
            for url in txt.split():
                got = url.find("http://")
                if got != -1:
                    logging.debug("wave - found url - %s" % str(url))
                    start = txt.find(url.strip())
                    if url.endswith(">"): annotations.append((start+2, start+len(url)-1, "link/manual", url[1:-1]))
                    else: annotations.append((start, start+len(url), "link/manual", url))
        except Exception, ex: handle_exception()
        logging.debug("annotations used: %s", annotations)
        reply = wavelet.reply(txt)
        if annotations:
            for ann in annotations:
                if ann[0]:
                    try: reply.range(ann[0], ann[1]).annotate(ann[2], ann[3])
                    except Exception, ex: handle_exception()
        logging.info("submitting to server: %s" % wavelet.serialize())
        try:
            import google
            self.submit(wavelet)
        except google.appengine.api.urlfetch_errors.DownloadError: handle_exception()

    def outnocb(self, waveid, txt, result=[], event=None, origin="", dot=", ", *args, **kwargs):
        """ output to the root id. """
        if not self.domain in self._server_rpc_base:
            rpc_base = credentials.RPC_BASE[waveid.split("!")[0]]
            self._server_rpc_base = rpc_base
            logging.warn("%s - %s - server_rpc_base is %s" % (self.name, waveid, self._server_rpc_base))
        if not event:
            event = WaveEvent()
            event.channel = event.printto = waveid
            event.txt = event.origtxt = txt
            event.auth = event.userhost = origin or self.me
            event.bind(self)
        self._raw(txt, event)

    def toppost(self, waveid, txt):
        """ output to the root id. """
        if not self.domain in waveid:
            logging.warn("%s - not connected - %s" % (self.name, waveid))
            return
        wave = Wave(waveid)
        if wave and wave.data.waveid: wave.toppost(self, txt)
        else: logging.warn("%s - we are not joined to %s" % (self.name, waveid))

    def newwave(self, domain=None, participants=None, submit=False):
        """ create a new wave. """
        logging.info("wave - new wave on domain %s" % domain)
        newwave = self.new_wave(domain or self.domain, participants=participants, submit=submit)
        return newwave

    def run(self):
        """ start the bot on the runner. """
        appengine_robot_runner.run(self, debug=True, extra_handlers=[])
