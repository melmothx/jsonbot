# jsb/plugs/test.py
# encoding: utf-8
#

""" test plugin. """

from jsb.utils.exception import exceptionmsg, handle_exception, exceptionevents, exceptionlist
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.eventbase import EventBase
from jsb.lib.users import users
from jsb.lib.threads import start_new_thread
from jsb.utils.generic import waitforqueue, waitevents
from jsb.lib.runner import cmndrunner, defaultrunner

## basic imports

import time
import random
import copy
import logging

## defines

cpy = copy.deepcopy

donot = ['privmsg', 'notice', 'disable', 'deadline', 'twitter', 'stop', 'admin', 'quit', 'reboot', 'shutdown', 'exit', 'delete', 'halt', 'upgrade', \
'install', 'reconnect', 'wiki', 'weather', 'sc', 'jump', 'disable', 'dict', \
'snarf', 'validate', 'popcon', 'twitter', 'tinyurl', 'whois', 'rblcheck', \
'wowwiki', 'wikipedia', 'tr', 'translate', 'serie', 'sc', 'shoutcast', 'mash', \
'gcalc', 'identi', 'mail', 'part', 'cycle', 'exception', 'fleet', 'ln', 'markov-learn', 'pit', 'bugtracker', 'tu', 'banner', 'test', 'cloud', 'dispatch', 'lns', 'loglevel', \
'cloneurl', 'clone', 'hb', 'rss-all', 'rss-get', 'rss-sync', 'rss-add', 'rss-register', 'rss-cloneurl', 'rss-scan']

errors = {}
teller = 0

def dummy(a, b=None):
    return ""

## dotest function

def dotest(bot, event):
    global teller
    global errors
    match = ""
    waiting = []
    if True:
        examplez = examples.getexamples()
        random.shuffle(examplez)
        #logging.warn("test - running examples: %s" % ", ".join(examplez))
        for example in examplez:
            time.sleep(0.001)
            if match and match not in example: continue
            skip = False
            for dont in donot:
                if dont in example: skip = True
            if skip: continue
            teller += 1
            event.reply('command: ' + example)
            e = cpy(event)
            e.txt = example
            e.speed = 6
            e.bind(bot)
            bot.put(e)
            waiting.append(e)
            teller += 1
        if not bot.isgae: waitevents(waiting)
        event.reply("%s commands executed" % teller)
    if errors:
        event.reply("there are %s errors .. " % len(errors))
        for cmnd, error in errors.iteritems(): event.reply("%s - %s" % (cmnd, error))
    for (event, msg) in exceptionevents: event.reply("EXCEPTION: %s - %s" % (event.txt,msg))
    for msg in exceptionlist: event.reply("EXCEPTION: %s" % msg)

## test-plugs command

def handle_testplugs(bot, event):
    """ test the plugins by executing all the available examples. """
    bot.plugs.loadall(force=True)
    global teller
    try: loop = int(event.args[0])
    except (ValueError, IndexError): loop = 1
    try: threaded = event.args[1]
    except (ValueError, IndexError): threaded = 0
    threads = []
    teller = 0
    event.dontclose = True
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

cmnds.add('test-plugs', handle_testplugs, ['TEST', ], threaded=True)
examples.add('test-plugs', 'test all plugins by running there examples', 'test-plugs')

## test-forcedconnection command

def handle_forcedreconnect(bot, ievent):
    """ do a forced reconnect. """
    if not bot.ssl: bot.sock.shutdown(2)
    else: bot.sock.shutdown()

cmnds.add('test-forcedreconnect', handle_forcedreconnect, 'TEST')

## test-forcedexception command

def handle_forcedexception(bot, ievent):
    """ raise a exception. """
    raise Exception('test exception')

cmnds.add('test-forcedexception', handle_forcedexception, 'TEST')
examples.add('test-forcedexception', 'throw an exception as test', 'test-forcedexception')

## test-wrongxml command

def handle_testwrongxml(bot, ievent):
    """ try sending borked xml. """
    if not bot.type == "sxmpp":
        ievent.reply('only sxmpp')
        return
    ievent.reply('sending bork xml')
    bot._raw('<message asdfadf/>')

cmnds.add('test-wrongxml', handle_testwrongxml, 'TEST')

## test-unicode command

def handle_testunicode(bot, ievent):
    """ send unicode test down the output paths. """
    outtxt = u"Đíť ìš éèñ ëņċøďıńğŧęŝţ· .. にほんごがはなせません .. ₀0⁰₁1¹₂2²₃3³₄4⁴₅5⁵₆6⁶₇7⁷₈8⁸₉9⁹ .. ▁▂▃▄▅▆▇▉▇▆▅▄▃▂▁ .. .. uǝʌoqǝʇsɹǝpuo pɐdı ǝɾ ʇpnoɥ ǝɾ"
    ievent.reply(outtxt)
    bot.say(ievent.channel, outtxt, event=ievent)

cmnds.add('test-unicode', handle_testunicode, 'TEST')
examples.add('test-unicode', 'test if unicode output path is clear', 'test-unicode')

## test-docmnd command

def handle_testdocmnd(bot, ievent):
    """ call bot.docmnd(). """
    if ievent.rest: bot.docmnd(ievent.origin or ievent.userhost, ievent.channel, ievent.rest, event=ievent)
    else: ievent.missing("<cmnd>")

cmnds.add('test-docmnd', handle_testdocmnd, 'TEST')
examples.add('test-docmnd', 'test the bot.docmnd() method', 'test-docmnd version')

## test-say command

def handle_testsay(bot, ievent):
    if not ievent.rest:
        ievent.missing("<txt>")
        return
    bot.say(ievent.printto, ievent.rest)

cmnds.add('test-say', handle_testsay, 'TEST')
examples.add('test-say', 'use bot.say()', 'test-say')

## test-options command

def handle_testoptions(bot, ievent):
    ievent.reply('"%s" - %s' % (ievent.txt, unicode(ievent.options)))

cmnds.add('test-options', handle_testoptions, 'TEST')
examples.add('test-options', "test event options", "test-options")

## test-deadline command

def handle_testdeadline(bot, ievent):
    ievent.reply('starting 40 sec sleep')
    time.sleep(40)

cmnds.add('test-deadline', handle_testdeadline, 'TEST')
examples.add('test-deadline', "sleep 40 sec to trigger deadlineexceeded exception (GAE)", "test-deadline")

## test-xhtml command

def handle_testhtml(bot, ievent):
    if not ievent.rest: data = '<span style="font-family: fixed; font-size: 10pt"><b>YOOOO BROEDERS</b></span>'
    else: data = ievent.rest
    ievent.reply(data, html=True)

cmnds.add('test-html', handle_testhtml, 'TEST')
examples.add('test-html', 'test html output', '1) test-html 2) test-html <h1><YOO</h1>')

def handle_testuuid(bot, ievent):
    import uuid
    ievent.reply(uuid.uuid4())

cmnds.add('test-uuid', handle_testuuid, 'TEST')

def handle_testthreaded(bot, ievent):
    ievent.reply("yoooo!")

cmnds.add("test-threaded", handle_testthreaded, "TEST", threaded=True)
