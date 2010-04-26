#!/usr/bin/env python
#
#

""" test the test plugin. """

## vars

## boot

import os
import sys
sys.path.insert(0, os.getcwd())
os.chdir("..")
sys.path.insert(0, os.getcwd())

## lib imports

from gozerlib.config import Config
from gozerlib.plugins import Plugins
from gozerlib.gae.wave.bot import WaveBot
from gozerlib.gae.wave.event import WaveEvent
from gozerlib.utils.generic import stringinlist
from gozerlib.utils.exception import handle_exception
from gozerlib.errors import NoSuchWave, NoSuchCommand
from gozerlib.threads import start_new_thread
from gozerlib.utils.log import setloglevel

## basic imports

import unittest
import logging

## unittests

class test_pipeline(unittest.TestCase):


    def setUp(self):
        setloglevel("error")

    def test_wave(self):
        plugs = Plugins()
        plugs.loadall(["commonplugs", 'gozerlib.plugs'])
        cfg = Config()
        cfg.owner = "test@test"
        bot = WaveBot(cfg=cfg, plugs=plugs)
        bot.setstate()
        bot.allowall = True
        event = WaveEvent()
        event.bot = bot
        event.txt = "!list | grep c"
        event.makeargs()
        result = bot.doevent(event)
        logging.error(str(result))
        self.assert_(stringinlist('welcome', result))

if __name__ == '__main__':
    unittest.main()
