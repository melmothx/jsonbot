# gozerlib/utils/opts.py
#
#

""" options related functions. """

## gozerlib imports

from gozerlib.config import Config
from gozerlib.utils.generic import getversion

## basic imports

import os

## functions

def makeopts():
    from optparse import OptionParser
    parser = OptionParser(usage='usage: %prog [options]', version='%prog ' + getversion())
    parser.add_option('', '-r', type='string', default=False, dest='doresume', 
                  metavar='PATH', 
                  help="resume the bot from the folder specified")
    parser.add_option('-u', '--user', type='string', default=False,
dest='user', 
                  help="owner of the bot")
    parser.add_option('-o', '--owner', type='string', default=False,
dest='owner', 
                  help="owner of the bot")
    parser.add_option('-s', '--server', type='string', default=False,
dest='server', 
                  help="server to connect to (irc)")
    parser.add_option('-c', '--channel', type='string', default=False,
dest='channel', 
                  help="channel to join")
    parser.add_option('-l', '--loglevel', type='string', default=False,
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
    parser.add_option('-f', '--fleet', action='store_true', default=False,
dest='fleet', 
                  help="add bot to the fleet")
    parser.add_option('-a', '--ssl', action='store_true', default=False,
dest='ssl', 
                  help="use ssl")
    parser.add_option('-y', '--nossl', action='store_true', default=False,
dest='nossl', 
                  help="don't use ssl")
    parser.add_option('-x', '--exec', type='string', default="",
dest='command', help="give a command to execute")

    opts, args = parser.parse_args()
    opts.args = args
    return opts

def makeconfig(opts):
    name = opts.name or 'default-SXMPPBot'
    cfg = Config('fleet' + os.sep + name + os.sep + 'config')
    cfg.name = name

    if opts.user:
        cfg.user = opts.user

    if not cfg.user:
        print "user needs to be set .. see the -u option."
        os._exit(1)

    if opts.user:
        try:
            cfg.host = opts.user.split('@')[1]
        except ValueError:
            print "user is not in the nick@server format"
            os._exit(1)

    if not cfg.host:
        try:
            cfg.host = cfg.user.split('@')[1]
        except ValueError:
            print "user is not in the nick@server format"
            os._exit(1)

    if opts.password:
        cfg.password = opts.password

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

    return cfg
