# jsb/plugs/common/colors.py
#
#

""" use the morph to add color to selected words. """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.callbacks import first_callbacks
from jsb.lib.morphs import outputmorphs
from jsb.lib.persiststate import PlugState
from jsb.utils.lazydict import LazyDict

## defines

state = PlugState()
state.define("colormapping", {})

colors = LazyDict({
    "ERASE_LINE": '\033[2K',
    "BOLD": '\033[1m',
    "RED": '\033[91m',
    "YELLOW": '\033[93m',
    "GREEN": '\033[92m',
    "ENDC": '\033[0m'
})

## the morph

def docolormorph(txt):
    if not txt: return txt
    result = txt
    for t, color in state.data.colormapping.iteritems():
        try:
            rep = colors[color] + t + colors.ENDC
            result = txt.replace(t, rep)
        except KeyError: logging.warn("colors - can't find color %s" % color)
    return result

## color-list command

def handle_colorlist(bot, event):
    event.reply("colors set: ", state.data.colormapping)

cmnds.add("color-list", handle_colorlist, ["OPER"])
examples.add("color-list", "show color mapping", "color-list")

## color-add command

def handle_coloradd(bot, event):
    try: (txt, color) = event.rest.rsplit(" ", 1)
    except (TypeError, ValueError): event.missing("<txt> <color>") ; return
    state.data.colormapping[txt] = color.upper()
    state.save()
    event.reply("color set to %s" % color)

cmnds.add("color-add", handle_coloradd, ["OPER"])
examples.add("color-add", "add a text color replacement to the morphs", "color-add dunker red")

## color-del command

def handle_colordel(bot, event):
    if not event.rest: event.missing("<txt>") ; return
    try: del state.data.colormapping[event.rest] ; state.save()
    except KeyError: event.reply("we are not morphing %s" % event.rest)
    event.reply("color removed for %s" % event.rest)

cmnds.add("color-del", handle_colordel, ["OPER"])
examples.add("color-del", "remove a text color replacement from the morphs", "color-del dunker")

## start

def init():
    outputmorphs.add(docolormorph)

def bogus(bot, event):
    pass

first_callbacks.add("START", bogus)
