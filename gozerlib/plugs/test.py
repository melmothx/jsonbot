# gozerlib/plugs/test.py
# encoding: utf-8
#

""" test plugin. """

from gozerlib.utils.exception import exceptionmsg, handle_exception
from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.eventbase import EventBase
from gozerlib.users import users
from gozerlib.threads import start_new_thread
from gozerlib.socklib.utils.generic import waitforqueue

## basic imports

import time
import random
import copy

## defines

cpy = copy.deepcopy

donot = ['quit', 'reboot', 'shutdown', 'exit', 'delete', 'halt', 'upgrade', \
'install', 'reconnect', 'wiki', 'weather', 'sc', 'jump', 'disable', 'dict', \
'snarf', 'validate', 'popcon', 'twitter', 'tinyurl', 'whois', 'rblcheck', \
'wowwiki', 'wikipedia', 'tr', 'translate', 'serie', 'sc', 'shoutcast', 'mash', \
'gcalc', 'identi', 'mail', 'part', 'cycle', 'exception', 'fleet', 'ln', 'markov-learn', 'pit', 'bugtracker', 'tu', 'banner', 'test', 'cloud', 'dispatch', 'lns', 'loglevel', \
'cloneurl', 'clone', 'hb', 'rss-get', 'rss-sync']

def dummy(a, b=None):
    return ""

## commands

def handle_testplugs(bot, event):
    #if bot.cfg['type'] == 'irc' and not event.isdcc:
    #    event.reply('use this command in a /dcc chat with the bot')
    #    return
    #if bot.cfg['type'] == 'web':
    #    event.reply("don't use this command on a web bot")
    #    return
    #if bot.cfg['type'] == 'wave':
    #    event.reply("don't use this command on a wave bot")
    #    return
    match = ""
    try:
        loop = int(event.args[0])
    except (ValueError, IndexError):
        loop = 1
    teller = 0
    errors = {}
    msg = cpy(event)
    for i in range(loop):
        event.reply('starting loop %s' % str(i))
        examplez = examples.getexamples()
        random.shuffle(examplez)
        for example in examplez:
            if match and match not in example:
                continue
            skip = False
            for dont in donot:
                if dont in example:
                    skip = True
            if skip:
                continue
            teller += 1
            event.reply('command: ' + example)
            try:
                msg.txt = "!" + example
                bot.docmnd(event.userhost, event.channel, example, msg)
            except Exception, ex:
                errors[example] = exceptionmsg()
    event.reply('%s tests run' % teller)
    if errors:
        event.reply("there are %s errors .. " % len(errors))
        for cmnd, error in errors.iteritems():
            event.reply("%s - %s" % (cmnd, error))
    else:
        event.reply("no errors")

    event.outqueue.put_nowait(None)

cmnds.add('test-plugs', handle_testplugs, ['USER', ], threaded=True)
examples.add('test-plugs', 'test all plugins by running there examples', 'test-plugs')

def handle_forcedreconnect(bot, ievent):
    if bot.type == "sxmpp":
        bot.disconnectHandler(Exception('test exception for reconnect'))
    else:
        bot.sock.shutdown(2)

cmnds.add('test-forcedreconnect', handle_forcedreconnect, 'OPER')

def handle_forcedexception(bot, ievent):
    raise Exception('test exception')

cmnds.add('test-forcedexception', handle_forcedexception, 'OPER')
examples.add('test-forcedexception', 'throw an exception as test', 'test-forcedexception')

def handle_testwrongxml(bot, ievent):
    if not bot.type == "sxmpp":
        ievent.reply('only sxmpp')
        return
    ievent.reply('sending bork xml')
    bot._raw('<message asdfadf/>')

cmnds.add('test-wrongxml', handle_testwrongxml, 'OPER')

def handle_tojson(bot, ievent):
    ievent.reply(str(ievent.dump()))

cmnds.add('test-json', handle_tojson, 'OPER')
examples.add('test-json', "dump the event as json", "test-json")

def handle_testunicode(bot, ievent):
    outtxt = u"Đíť ìš éèñ ëņċøďıńğŧęŝţ· .. にほんごがはなせません .. ₀0⁰₁1¹₂2²₃3³₄4⁴₅5⁵₆6⁶₇7⁷₈8⁸₉9⁹ .. ▁▂▃▄▅▆▇▉▇▆▅▄▃▂▁ .. .. uǝʌoqǝʇsɹǝpuo pɐdı ǝɾ ʇpnoɥ ǝɾ .. AВы хотите говорить на русском языке, товарищ?"
    ievent.reply(outtxt)
    bot.say(ievent.channel, outtxt)

cmnds.add('test-unicode', handle_testunicode, 'OPER')
examples.add('test-unicode', 'test if unicode output path is clear', 'test-unicode')

def handle_testdocmnd(bot, ievent):
    if ievent.rest:
        bot.docmnd(ievent.origin, ievent.channel, ievent.rest)
    else:
        ievent.missing("<cmnd>")

cmnds.add('test-docmnd', handle_testdocmnd, 'OPER')
examples.add('test-docmnd', 'test the bot.docmnd() method', 'test-docmnd version')
