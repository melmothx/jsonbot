# jsb/plugs/common/geo.py
#
#

""" This product includes GeoLite data created by MaxMind, available from http://maxmind.com/ """


## jsb imports

from jsb.lib.callbacks import callbacks
from jsb.lib.commands import cmnds
from jsb.utils.url import geturl2
from jsb.imports import getjson

## system imports
from socket import gethostbyname
import re
## defines

URL = "http://geoip.pidgets.com/?ip=%s&format=json"

def querygeoipserver(ip):
    ipinfo = getjson().loads(geturl2(URL % ip))
    return ipinfo

def host2ip(query):
    ippattern =   re.match(r"^([0-9]{1,3}\.){3}[0-9]{1,3}$", query)
    hostpattern = re.match(r"(\w+://)?(?P<hostname>\S+\.\w+)", query)
    ip = ""
    if ippattern: ip = ippattern.group(0)
    elif hostpattern:
        try: ip = gethostbyname(hostpattern.group('hostname'))
        except: pass
    return ip

## geo command

def handle_geo(bot, event):
    """ do a geo lookup. """
    if not event.rest: 
        event.missing("<ip>")
        return
    query = event.rest.strip()
    ip = host2ip(query)
    if not ip: event.reply("Couldn't look up the hostname") ; return
    event.reply("geo of %s is: " % ip, querygeoipserver(ip))

cmnds.add("geo", handle_geo, ["OPER", "GEO"])

def handle_geoPRE(bot, event):
    if event.chan.data.dogeo: return True 

def handle_geoJOIN(bot, event):
    event.reply("geo - doing query on %s" % event.hostname)
    result = querygeoipserver(host2ip(event.hostname))
    if result: event.reply("geo info: ", result)
    else: event.reply("no result")

callbacks.add("JOIN", handle_geoJOIN, handle_geoPRE)

def handle_geoon(bot, event):
    """ enable geo lookup on JOIN. """
    event.chan.data.dogeo = True
    event.chan.save()
    event.done()

cmnds.add("geo-on", handle_geoon, ["OPER"])

def handle_geooff(bot, event):
    """ disable geo lookup on JOIN. """
    event.chan.data.dogeo = False
    event.chan.save()
    event.done()

cmnds.add("geo-off", handle_geooff, ["OPER"])
