# plugs/gcalc.py
# encoding: utf-8
#
#

""" use google to calculate e.g. !gcalc 1 + 1 """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples
from gozerlib.utils.url import useragent

## basic imports

import urllib2

## gcalc command

def handle_gcalc(bot, ievent):
    """ use google calc . """
    if len(ievent.args) > 0: expr = " ".join(ievent.args).replace("+", "%2B").replace(" ", "+")
    else: ievent.missing('Missing an expression') ; return
    req = urllib2.Request("http://www.google.com/search?q=%s" % expr, None,  {'User-agent': useragent()})
    data = urllib2.urlopen(req).read()
    if "<img src=/images/calc_img.gif width=40 height=30 alt=\"\">" not in data: ievent.reply('Your expression can\'t be evaluated by the google calculator')
    else:
        ans = data.split("<img src=/images/calc_img.gif width=40 height=30 alt=\"\">")[1].split("<b>")[1].split("</b>")[0]
        ievent.reply(ans.replace('<font size=-2> </font>', '').replace('&#215;', '*').replace('<sup>', '**').replace('</sup>', ''))
    
cmnds.add('gcalc', handle_gcalc, ['USER', 'GUEST'])
examples.add('gcalc', 'calculate an expression using the google calculator', 'gcalc 1 + 1')
