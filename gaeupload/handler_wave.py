# handler_wave.py
#
#

""" this handler handles all the wave jsonrpc requests. """

## gozerlib imports

from gozerlib.utils.generic import getversion
from gozerlib.config import cfg
from gozerlib.errors import NoSuchCommand

## gaelib imports

from gozerlib.gae.wave.bot import WaveBot

## basic imports

import logging
import os

## defines

logging.warn(getversion('WAVE'))

# the bot

bot = WaveBot(domain=cfg.domain)

def main():
    bot.run()

if __name__ == "__main__":
    main()
