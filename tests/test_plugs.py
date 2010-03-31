#!/usr/bin/env python
#
#

""" test the test plugin. """

## vars

skip = ['hb-register', 'hb-subscribe', 'hb-add', 'hb-clone', 'hb-get', 'wikipedia', 'tinyurl']

## boot

import os
import sys
olddir = os.getcwd()
sys.path.insert(0, olddir)
#os.chdir("..")
#sys.path.append(os.getcwd())

## lib imports

from gozerlib.plugins import Plugins
from gozerlib.botbase import BotBase
from gozerlib.utils.generic import stringinlist
from gozerlib.utils.exception import handle_exception
from gozerlib.errors import NoSuchWave, NoSuchCommand
from gozerlib.threads import start_new_thread
from gozerlib.utils.log import setloglevel
from gozerlib.config import Config

## basic imports

import unittest

## unittests

setloglevel("error")

class test_plugs(unittest.TestCase):

    def setUp(self):
        setloglevel("error")

    def test_plugs(self):
        plugs = Plugins()
        plugs.loadall(["commonplugs", 'gozerlib.plugs'])
        cfg = Config()
        cfg.owner = "test@test"
        bot = BotBase(cfg, plugs=plugs)
        bot.setstate()
        bot.allowall = True
        threads = []
        from gozerlib.examples import examples
        for example in examples.getexamples():
            cmnd = example.split()[0]
            if cmnd in skip:
                continue
            try:
                bot._raw("executing %s" % example)
                threads.append(start_new_thread(bot.docmnd, ('test@test', '#test', example)))
            except (NoSuchWave, NoSuchCommand):
                pass
            except Exception, ex:
                handle_exception()
        for t in threads:
            t.join()

        self.assert_(not bot.error)

if __name__ == '__main__':
    unittest.main()
