# jsb/plugs/common/geo.py
#
#

""" This product includes GeoLite data created by MaxMind, available from http://maxmind.com/ """


## jsb imports

from jsb.lib.commands import cmnds
from jsb.utils.url import geturl2
from jsb.imports import getjson

## defines

URL = "http://geoip.pidgets.com/?ip=%s&format=json"

## geo command

def handle_geo(bot, event):
    if not event.rest: event.missing("<ip>") ; return
    event.reply("geo of %s is: " % event.rest, getjson().loads(geturl2(URL % event.rest)))

cmnds.add("geo", handle_geo, ["OPER", "GEO"])
