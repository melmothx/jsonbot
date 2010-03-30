# gozerlib/wave/waves.py
#
#

""" class to repesent a wave. """

## gozerlib imports

from gozerlib.channelbase import ChannelBase
from gozerlib.utils.exception import handle_exception
## 

from simplejson import dumps

## google imports

import google

## basic imports

import logging
import copy
import os

cpy = copy.deepcopy

class Wave(ChannelBase):

    """ a wave is seen as a channel. """

    def __init__(self, id):
        ChannelBase.__init__(self, 'gozerdata' + os.sep + 'waves' + os.sep + id)
        
    def parse(self, event, wavelet):

        """ parse event into a Wave. """

        self.data.id = self.id
        self.data.json_data = event.json
        self.data.title = wavelet._title
        self.data.waveid = wavelet._wave_id
        self.data.waveletid = wavelet._wavelet_id
        logging.debug("parsed %s (%s) channel" % (self.id, self.data.title))
        return self

    def say(self, bot, txt):

        """ output some txt to the wave. """

        if self.data.json_data:
            logging.debug("wave - say - using BLIND - %s" % self.data.json_data) 
            wavelet = bot.blind_wavelet(self.data.json_data)
        else:
            logging.info("did not join channel %s" % self.id)
            return

        if not wavelet:
            logging.error("cant get wavelet")
            return

        logging.warn('wave - out - %s - %s' % (self.data.title, txt))
        wavelet.reply(txt)

        try:
            bot.submit(wavelet)
        except google.appengine.api.urlfetch_errors.DownloadError:
            handle_exception()
            #pass

    def toppost(self, bot, txt):

        """ output some txt to the wave. """

        if self.data.json_data:
            logging.debug("wave - say - using BLIND - %s" % self.data.json_data) 
            wavelet = bot.blind_wavelet(self.data.json_data)
        else:
            logging.info("did not join channel %s" % self.id)
            return

        if not wavelet:
            logging.error("cant get wavelet")
            return

        logging.warn('wave - out - %s - %s' % (self.data.title, txt))

        try:
            blip = wavelet._root_blip.reply()
            blip.append(txt)
            bot.submit(wavelet)
        except google.appengine.api.urlfetch_errors.DownloadError:
            handle_exception()
            #pass
