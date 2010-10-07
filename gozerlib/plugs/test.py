# gozerlib/plugs/test.py
# encoding: utf-8
#

""" test plugin. """

from gozerlib.utils.exception import exceptionmsg, handle_exception, exceptionevents
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.eventbase import EventBase
from gozerlib.users import users
from gozerlib.threads import start_new_thread
from gozerlib.socklib.utils.generic import waitforqueue
from gozerlib.runner import cmndrunner, defaultrunner

## basic imports

import time
import random
import copy
import logging

## defines

cpy = copy.deepcopy

donot = ['twitter', 'stop', 'admin', 'quit', 'reboot', 'shutdown', 'exit', 'delete', 'halt', 'upgrade', \
'install', 'reconnect', 'wiki', 'weather', 'sc', 'jump', 'disable', 'dict', \
'snarf', 'validate', 'popcon', 'twitter', 'tinyurl', 'whois', 'rblcheck', \
'wowwiki', 'wikipedia', 'tr', 'translate', 'serie', 'sc', 'shoutcast', 'mash', \
'gcalc', 'identi', 'mail', 'part', 'cycle', 'exception', 'fleet', 'ln', 'markov-learn', 'pit', 'bugtracker', 'tu', 'banner', 'test', 'cloud', 'dispatch', 'lns', 'loglevel', \
'cloneurl', 'clone', 'hb', 'rss-get', 'rss-sync', 'rss-add', 'rss-register']

errors = {}
teller = 0

def dummy(a, b=None):
    return ""

## dotest function

def dotest(bot, event):
    global teller
    global errors
    match = ""
    msg = cpy(event)
    if True:
        examplez = examples.getexamples()
        random.shuffle(examplez)
        logging.warn("test - running examples: %s" % ", ".join(examplez))
        for example in examplez:
            if match and match not in example: continue
            skip = False
            for dont in donot:
                if dont in example: skip = True
            if skip: continue
            teller += 1
            event.reply('command: ' + example)
            try:
                msg.txt = "!" + example
                msg.bind(bot)
                bot.docmnd(event.auth or event.userhost, event.channel, example, msg)
            except Exception, ex: errors[example] = exceptionmsg()
    if errors:
        event.reply("there are %s errors .. " % len(errors))
        for cmnd, error in errors.iteritems(): event.reply("%s - %s" % (cmnd, error))
    for (event, msg) in exceptionevents: event.reply("EXCEPTION: %s - %s" % (event.txt,msg))

## test-plugs command

def handle_testplugs(bot, event):
    """ test the plugins by executing all the available examples. """
    bot.plugs.loadall()
    global teller
    try: loop = int(event.args[0])
    except (ValueError, IndexError): loop = 1
    try: threaded = event.args[1]
    except (ValueError, IndexError): threaded = 0
    threads = []
    teller = 0
    for i in range(loop):
        if threaded: threads.append(start_new_thread(dotest, (bot, event)))
        else: dotest(bot, event)
    if threads:
        for thread in threads: thread.join()
    event.reply('%s tests run' % teller)
    if errors:
        event.reply("there are %s errors .. " % len(errors))
        for cmnd, error in errors.iteritems(): event.reply("%s - %s" % (cmnd, error))
    else: event.reply("no errors")
    event.outqueue.put_nowait(None)

cmnds.add('test-plugs', handle_testplugs, ['USER', ], threaded=True)
examples.add('test-plugs', 'test all plugins by running there examples', 'test-plugs')

## test-forcedconnection command

def handle_forcedreconnect(bot, ievent):
    """ do a forced reconnect. """
    bot.sock.shutdown(2)

cmnds.add('test-forcedreconnect', handle_forcedreconnect, 'OPER')

## test-forcedexception command

def handle_forcedexception(bot, ievent):
    """ raise a exception. """
    raise Exception('test exception')

cmnds.add('test-forcedexception', handle_forcedexception, 'OPER')
examples.add('test-forcedexception', 'throw an exception as test', 'test-forcedexception')

## test-wrongxml command

def handle_testwrongxml(bot, ievent):
    """ try sending borked xml. """
    if not bot.type == "sxmpp":
        ievent.reply('only sxmpp')
        return
    ievent.reply('sending bork xml')
    bot._raw('<message asdfadf/>')

cmnds.add('test-wrongxml', handle_testwrongxml, 'OPER')

## test-unicode command

def handle_testunicode(bot, ievent):
    """ send unicode test down the output paths. """
    outtxt = u"Đíť ìš éèñ ëņċøďıńğŧęŝţ· .. にほんごがはなせません .. ₀0⁰₁1¹₂2²₃3³₄4⁴₅5⁵₆6⁶₇7⁷₈8⁸₉9⁹ .. ▁▂▃▄▅▆▇▉▇▆▅▄▃▂▁ .. .. uǝʌoqǝʇsɹǝpuo pɐdı ǝɾ ʇpnoɥ ǝɾ"
    ievent.reply(outtxt)
    bot.say(ievent.channel, outtxt)

cmnds.add('test-unicode', handle_testunicode, 'OPER')
examples.add('test-unicode', 'test if unicode output path is clear', 'test-unicode')

## test-docmnd command

def handle_testdocmnd(bot, ievent):
    """ call bot.docmnd(). """
    if ievent.rest: bot.docmnd(ievent.origin or ievent.userhost, ievent.channel, ievent.rest)
    else: ievent.missing("<cmnd>")

cmnds.add('test-docmnd', handle_testdocmnd, 'OPER')
examples.add('test-docmnd', 'test the bot.docmnd() method', 'test-docmnd version')

## test-bork command

def handle_testbork(bot, ievent):
    txtlist = ["\00%s" % i for i in range(40)]
    ievent.reply("borkers: 0 \000 1 \001 2 \002 3 \003 4 \004 5 \005 6 \006 7 \007 8 \008 9 \009 10 \010 11 \011 12 \012 13 \013 14 \014 15 \015 16 \016 17 \017 18 \018 19 \019 20 \020 21 \021 22 \022 23 \023 24 \024 25 \025 26 \026 27 \027 28 \028 29 \029 30 \030 31 \031")
    bot.say(ievent.channel, "borkers: 0 \000 1 \001 2 \002 3 \003 4 \004 5 \005 6 \006 7 \007 8 \008 9 \009 10 \010 11 \011 12 \012 13 \013 14 \014 15 \015 16 \016 17 \017 18 \018 19 \019 20 \020 21 \021 22 \022 23 \023 24 \024 25 \025 26 \026 27 \027 28 \028 29 \029 30 \030 31 \031")

cmnds.add('test-bork', handle_testbork, 'OPER')
examples.add('test-bork', 'send all possible ascii chars', 'test-bork')

## test-say command

def handle_testsay(bot, ievent):
    if not ievent.rest:
        ievent.missing("<txt>")
        return
    bot.say(ievent.printto, ievent.rest)

cmnds.add('test-say', handle_testsay, 'OPER')
examples.add('test-say', 'use bot.say()', 'test-say')
