# gozerlib/utils/opts.py
#
#

""" options related functions. """

## gozerlib imports

from gozerlib.errors import NameNotSet
from gozerlib.config import Config
from gozerlib.utils.generic import getversion
from gozerlib.utils.name import stripname

## basic imports

import os
import uuid

## functions

def makeopts():
    from optparse import OptionParser
    parser = OptionParser(usage='usage: %prog [options]', version='%prog ' + getversion())
    parser.add_option('', '-r', type='string', default=False, dest='doresume', 
                  metavar='PATH', 
                  help="resume the bot from the folder specified")
    parser.add_option('-u', '--user', type='string', default=False,
dest='user', 
                  help="JID of the bot")
    parser.add_option('-o', '--owner', type='string', default=False,
dest='owner', 
                  help="owner of the bot")
    parser.add_option('-s', '--server', type='string', default=False,
dest='server', 
                  help="server to connect to (irc)")
    parser.add_option('-c', '--channel', type='string', default=False,
dest='channel', 
                  help="channel to join")
    parser.add_option('-l', '--loglevel', type='string', default="warning",
dest='loglevel', 
                  help="loglevel of the bot .. the lower the more it logs")
    parser.add_option('-p', '--password', type='string', default=False,
dest='password', 
                  help="set password used to connect to the server")
    parser.add_option('-n', '--name', type='string', default=False, 
dest='name', 
                  help="bot's name")
    parser.add_option('', '--port', type='string', default=False,
dest='port', 
                  help="set port of server to connect to")
    parser.add_option('', '--save', action='store_true', default=False,
dest='save', 
                  help="save to config file")
    parser.add_option('-a', '--all', action='store_true', default=False,
dest='all', 
                  help="show available fleet bots")
    parser.add_option('', '--ssl', action='store_true', default=False,
dest='ssl', 
                  help="use ssl")
    parser.add_option('-y', '--nossl', action='store_true', default=False,
dest='nossl', 
                  help="don't use ssl")
    parser.add_option('-x', '--exec', type='string', default="",
dest='command', help="give a command to execute")
    parser.add_option('-t', '--type', type='string', default="console",
dest='type', help="define type of the bot")
    parser.add_option('-z', '--forward', action='store_true', default=False,
dest='forward', help="enable forwarding bot")
    parser.add_option('-6', '--ipv6', action='store_true', default=False,
dest='ipv6', help="enable ipv6 bot")

    opts, args = parser.parse_args()
    opts.args = args
    return opts

def makeconfig(type, opts, botname=None):
    if not botname:
        botname = opts.name or "default-%s" % str(type)
    botname = stripname(botname)
    cfg = Config('fleet' + os.sep + botname + os.sep + 'config')
    cfg.type = type
    cfg.botname = botname

    if opts.user:
        cfg.user = opts.user
    else:
        cfg.user = "%s@gozerbot.org" % cfg.uuid

    if opts.user:
        try:
            cfg.host = opts.user.split('@')[1]
        except ValueError:
            print "user is not in the nick@server format"

    if not cfg.host:
        try:
            cfg.host = cfg.user.split('@')[1]
        except ValueError:
            print "user is not in the nick@server format"

    if opts.password:
        cfg.password = opts.password
    else:
        cfg.password = cfg.password or str(uuid.uuid4())

    if opts.ssl:
        cfg.ssl = True

    if opts.nossl:
        cfg.ssl = False

    if opts.port:
        cfg.port = opts.port
    else:
        cfg.port = 6667

    if opts.server:
        cfg.server = opts.server
    else:
        cfg.server = cfg.server or "localhost"

    if opts.name:
        cfg.jid = opts.name

    if not cfg.owner:
        cfg.owner = []

    if opts.owner and opts.owner not in cfg.owner:
        cfg.owner.append(opts.owner)

    if opts.loglevel:
        cfg.loglevel = opts.loglevel
    else:
        cfg.loglevel = cfg.loglevel or "warning"

    if opts.ipv6:
        cfg.ipv6 = opts.ipv6

    return cfg
