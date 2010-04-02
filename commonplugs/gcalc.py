# plugs/gcalc.py
# encoding: utf-8
#
#

""" use google to calculate e.g. !gcalc 1 + 1 """

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.examples import examples

## basic imports

import urllib2

## commands

def handle_gcalc(bot, ievent):
    if len(ievent.args) > 0:
        expr = " ".join(ievent.args).replace("+", "%2B").replace(" ", "+")
    else:
        ievent.missing('Missing an expression')
        return
    
    req = urllib2.Request("http://www.google.com/search?q=%s" % expr, 
                          None, 
                          {'User-agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.11) Gecko/20071204 BonEcho/2.0.0.11'})
    data = urllib2.urlopen(req).read()
    
    if "<img src=/images/calc_img.gif width=40 height=30 alt=\"\">" not in data:
        ievent.reply('Your expression can\'t be evaluated by the google calculator')
    else:
        ans = data.split("<img src=/images/calc_img.gif width=40 height=30 alt=\"\">")[1].split("<b>")[1].split("</b>")[0]
        ievent.reply(ans.replace('<font size=-2> </font>', '').replace('&#215;', '*').replace('<sup>', '**').replace('</sup>', ''))

    return
    
cmnds.add('gcalc', handle_gcalc, ['USER', 'GUEST'])
examples.add('gcalc', 'calculate an expression using the google calculator', 'gcalc 1 + 1')
