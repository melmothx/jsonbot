#!/usr/bin/env python
#
#

import os.path

if os.path.isfile("/etc/debian_version") and os.path.isdir("/var/lib/jsb"):
    target = "/var/lib/jsb"
else:
    target = "jsb"

import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

upload = []

def uploadfiles(dir):
    upl = []
    if not os.path.isdir(dir): print "%s does not exist" % dir ; os._exit(1)
    for file in os.listdir(dir):
        if not file or file.startswith('.'):
            continue
        d = dir + os.sep + file
        if not os.path.isdir(d):
            if file.endswith(".pyc"):
                continue
            upl.append(d)

    return upl

def uploadlist(dir):
    upl = []

    for file in os.listdir(dir):
        if not file or file.startswith('.'):
            continue
        d = dir + os.sep + file
        if os.path.isdir(d):   
            upl.extend(uploadlist(d))
        else:
            if file.endswith(".pyc"):
                continue
            upl.append(d)

    return upl

setup(
    name='jsb',
    version='0.6b2',
    url='http://jsonbot.googlecode.com/',
    download_url="http://code.google.com/p/jsonbot/downloads", 
    author='Bart Thate',
    author_email='bthate@gmail.com',
    description='The bot for you!',
    license='MIT',
    scripts=['bin/jsb',
             'bin/jsb-init',
             'bin/jsb-irc', 
             'bin/jsb-fleet', 
             'bin/jsb-xmpp', 
             'bin/jsb-release',
             'bin/jsb-rollback',
             'bin/jsb-run',
             'bin/jsb-stop',
             'bin/jsb-udp',
             'bin/jsb-upgrade',
             'bin/jsb-upload',
             'bin/jsb-uploadall'],
    packages=['jsb',
              'jsb.lib', 
              'jsb.utils', 
              'jsb.lib.console',
              'jsb.lib.gae',
              'jsb.lib.gae.utils',
              'jsb.lib.gae.web',
              'jsb.lib.gae.wave',
              'jsb.lib.gae.xmpp',
              'jsb.lib.socklib',
              'jsb.lib.socklib.irc',
              'jsb.lib.socklib.xmpp',
              'jsb.lib.socklib.utils',
              'jsb.lib.socklib.rest',
              'jsb.contrib',
              'jsb.contrib.simplejson',
              'jsb.contrib.tweepy',
              'jsb.plugs',
              'jsb.plugs.core',
              'jsb.plugs.wave',
              'jsb.plugs.common',
              'jsb.plugs.socket', 
              'jsb.plugs.gae',
              'jsb.plugs.myplugs'],
    long_description = """ JSONBOT is a remote event-driven framework for building bots that talk JSON to each other over XMPP. IRC/Console/XMPP (shell) Wave/Web/XMPP (GAE) implementations provided. """,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: Other OS',
        'Programming Language :: Python',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    data_files=[(target + os.sep + 'data', uploadlist('jsb' + os.sep + 'data')),
                (target + os.sep + 'data' + os.sep + 'examples', uploadfiles('jsb' + os.sep + 'data' + os.sep + 'examples')),
                (target + os.sep + 'upload', uploadfiles('jsb' + os.sep + 'upload')),
                (target + os.sep + 'upload' + os.sep + 'webapp2', uploadlist('jsb' + os.sep + 'upload' + os.sep + 'webapp2')),
                (target + os.sep + 'upload' + os.sep + 'assets', uploadlist('jsb' + os.sep + 'upload' + os.sep + 'assets')),
                (target + os.sep + 'upload' + os.sep + 'templates', uploadlist('jsb' + os.sep + 'upload' + os.sep +'templates')),
                (target + os.sep + 'upload' + os.sep + 'waveapi', uploadlist('jsb' + os.sep + 'upload' + os.sep + 'waveapi')),
                (target + os.sep + 'upload' + os.sep + 'waveapi' + os.sep + 'oauth', uploadlist('jsb' + os.sep + 'upload' + os.sep + 'waveapi' + os.sep + 'oauth')),
                (target + os.sep + 'upload' + os.sep + 'waveapi' + os.sep + 'simplejson', uploadlist('jsb' + os.sep + 'upload' + os.sep + 'waveapi' + os.sep + 'simplejson')),
                (target + os.sep + 'upload' + os.sep + 'gadgets', uploadlist('jsb' + os.sep + 'upload' + os.sep + 'gadgets'))],
)
