# gozerlib/plugs/sort.py
#
# Sorting

""" sort bot results. """

__author__ = "Wijnand 'maze' Modderman <http://tehmaze.com>"
__license__ = "BSD"

## gozerlib imports

from gozerlib.commands import cmnds
from gozerlib.utils.generic import waitforqueue
from gozerlib.examples import examples

## basic imports

import optparse

## classes

class SortError(Exception): pass

class SortOptionParser(optparse.OptionParser):

    """ options parsers for the sort command. """

    def __init__(self):
        optparse.OptionParser.__init__(self)

        self.add_option('-f', '--ignore-case',
            help='fold lower case to upper case characters', default=False,
            action='store_true', dest='ignorecase')

        self.add_option('-n', '--numeric-sort', default=False,
            help='compare according to string numerical value', 
            action='store_true', dest='numeric')

        self.add_option('-r', '--reverse', default=False,
            help='reverse the result of comparisons', 
            action='store_true', dest='reverse')

        self.add_option('-u', '--unique', default=False,
            help='output only the first of an equal run', 
            action='store_true', dest='unique')

    def format_help(self, formatter=None):
        raise SortError('sort [-fnru] [--ignore-case] [--numeric-sort] [--reverse] [--unique]')

    def error(self, msg):
        return self.exit(msg=msg)

    def exit(self, status=0, msg=None):
        if msg:
            raise SortError(msg)
        else:
            raise SortError

## functions

def numeric_compare(x, y):
    try: a = int(x)
    except: return cmp(x, y)
    try: b = int(y)
    except: return cmp(x, y)
    return a - b

## commands

def handle_sort(bot, ievent):
    """ sort the result list. """
    parser = SortOptionParser()

    if not ievent.inqueue:
        if not ievent.args:
            ievent.missing('<input>')
            return
        try:
            options, result = parser.parse_args(ievent.args)
        except SortError, e:
            ievent.reply(str(e))
            return
    else:
        result = waitforqueue(ievent.inqueue, 30)
        try:
            options, args = parser.parse_args(ievent.rest.split())
        except SortError, e:
            ievent.reply(str(e))
            return

    if not result:
        ievent.reply('no data to sort')
        return

    if options.unique:
        result = list(set(result))
    if options.numeric:
        result.sort(numeric_compare)
    else:
        result.sort()
    if options.ignorecase:
        result.sort(lambda a, b: cmp(a.upper(), b.upper()))
    if options.reverse:
        result.reverse()
    
    ievent.reply("results: ", result)

cmnds.add('sort', handle_sort, ['USER', 'GUEST'], threaded=True)
examples.add('sort', 'sort the output of a command', 'list | sort')
