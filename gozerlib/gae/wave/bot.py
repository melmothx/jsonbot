# gozerlib/wave/bot.py
#
#

""" google wave bot. """

## gozerlib imports

from gozerlib.persist import Persist
from gozerlib.botbase import BotBase
from gozerlib.plugins import plugs
from gozerlib.utils.generic import getversion
from gozerlib.callbacks import callbacks
from gozerlib.outputcache import add
from gozerlib.config import Config

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
from google.appengine.ext import webapp
from waveapi import appengine_robot_runner
from django.utils import simplejson
from google.appengine.api import urlfetch

import config.credentials as credentials
import google
import waveapi

## generic imports

import logging
import cgi
import os
import time

## defines

waves = {}

class WaveBot(BotBase, robot.Robot):

    """ 
        bot to implement google wave stuff. 

        :param name: bot's name
        :type param: string
        :param image_url: url pointing to the bots image
        :type image_url: string
        :param version: the bots version 
        :type version: string
        :param profile_url: url pointing to the bots profile
        :type profile_url: string

    """

    def __init__(self, cfg=None, users=None, plugs=None, jid=None, domain=None,
                 image_url='http://jsonbot.appspot.com/assets/favicon.png',
                 profile_url='http://jsonbot.appspot.com/', *args, **kwargs):
        sname = 'jsonbot'
        BotBase.__init__(self, cfg, users, plugs, *args, **kwargs)
        self.type = 'wave'
        self.jid = jid

        if self.cfg:
            self.cfg['type'] = 'wave'
            self.cfg.save()

        self.type = "wave"

        if cfg:
            self.domain = cfg['domain'] or 'googlewave.com'
        else:
            self.domain = domain or 'googlewave.com'

        if self.cfg and self.cfg['domain'] != self.domain:
                self.cfg['domain'] = self.domain
                self.cfg.save()

        robot.Robot.__init__(self, name=sname, image_url=image_url, profile_url=profile_url)
        self.set_verification_token_info(credentials.verification_token[self.domain], credentials.verification_secret[self.domain])
        self.setup_oauth(credentials.Consumer_Key[self.domain], credentials.Consumer_Secret[self.domain],
                             server_rpc_base=credentials.RPC_BASE[self.domain])
        self.register_handler(events.BlipSubmitted, self.OnBlipSubmitted)
        self.register_handler(events.WaveletSelfAdded, self.OnSelfAdded)
        self.register_handler(events.WaveletParticipantsChanged, self.OnParticipantsChanged)
        self.iswave = True
        #self.channels = Persist("gozerstore" + os.sep + "fleet" + os.sep + self.name + os.sep + "channels")
        self.waves = waves
 
    def OnParticipantsChanged(self, event, wavelet):

        """ invoked when any participants have been added/removed. """

        wevent = WaveEvent()
        wevent.parse(self, event, wavelet)
        callbacks.check(self, wevent)

    def OnSelfAdded(self, event, wavelet):

        """ invoked when the robot has been added. """

        time.sleep(1)
        logging.warn('wave - joined "%s" (%s) wave' % (wavelet._wave_id, wavelet._title))

        wevent = WaveEvent()
        wevent.parse(self, event, wavelet)

        wave = Wave(wevent.waveid)
        wave.parse(event, wavelet)
        wave.save()

        wevent.append(
            element.Gadget('http://jsonbot.appspot.com/gadget.xml'))
        wevent.append('\n\nWelcome to JSONBOT\n\n')
        wevent.append('use the hb-register command to register a feed e.g. "hb-register slashdot http://rss.slashdot.org/Slashdot/slashdot"\n\n')
        wevent.append('see also the "help hubbub" command')

        callbacks.check(self, wevent)

    def OnBlipSubmitted(self, event, wavelet):

        """ new blip added. here is where the command dispatching takes place. """

        wevent = WaveEvent()
        wevent.parse(self, event, wavelet)
        wevent.auth = wevent.userhost

        wave = Wave(wevent.waveid)

        if not wave.data.title:
            wave.parse(event, wavelet)
            wave.save()

        if len(wevent.txt) >= 2:
            if self.cfg and self.cfg.cc and (wevent.txt[0] in self.cfg.cc):
                wevent.txt = wevent.txt[1:]
            elif wevent.txt[0] != '!':
                return
        else:
            return

        self.doevent(wevent)


    def say(self, waveid, txt):

        """
            output to the root id. 

            :param waveid: id of the wave 
            :type waveid: string
            :param txt: text to output
            :type txt: string
            :rtype: None

        """

        if not self.domain in self._server_rpc_base:
            rpc_base = credentials.RPC_BASE[waveid.split("!")[0]]
            self._server_rpc_base = rpc_base
            logging.warn("waces - %s - server_rpc_base is %s" % (waveid, self._server_rpc_base))
            
        wave = Wave(waveid)

        if wave and wave.data.waveid:
            wave.say(self, txt)
        else:
            logging.warn("we are not joined into %s" % waveid)

    def toppost(self, waveid, txt):

        """
            output to the root id. 

            :param waveid: id of the wave 
            :type waveid: string
            :param txt: text to output
            :type txt: string
            :rtype: None

        """

        if not self.domain in waveid:
            logging.warn("wave - not connected - %s" % waveid)
            return
            
        wave = Wave(waveid)

        if wave and wave.data.waveid:
            wave.toppost(self, txt)
        else:
            logging.warn("we are not joined to %s" % waveid)

    def newwave(self, domain=None, participants=None, submit=False):

        """
            create a new wave. 

        """

        logging.warn("wave - new wave on domain %s" % domain)
        newwave = self.new_wave(domain or self.domain, participants=participants, submit=submit)

        return newwave

    def run(self):
        appengine_robot_runner.run(self, debug=True, extra_handlers=[])
