#!/usr/bin/env python
#
#

from setuptools import setup
import glob
import os

upload = []

def uploadfiles(dir):
    upl = []
    
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

upload = uploadlist('gaeupload')

setup(
    name='jsonbot',
    version='0.5b2',
    url='http://jsonbot.googlecode.com/',
    download_url="http://code.google.com/p/jsonbot/downloads", 
    author='Bart Thate',
    author_email='bthate@gmail.com',
    description='The JSON everywhere bot!',
    license='MIT',
    scripts = ['bin/jsb',
               'bin/jsb-edit',
               'bin/jsb-import',
               'bin/jsb-installplug',
               'bin/jsb-irc', 
               'bin/jsb-fleet', 
               'bin/jsb-xmpp', 
               'bin/jsb-release',
               'bin/jsb-rollback',
               'bin/jsb-run',
               'bin/jsb-stop',
               'bin/jsb-udp',
               'bin/jsb-upload',
               'bin/jsb-uploadall'],
    packages=['gozerlib', 
              'gozerlib.utils', 
              'gozerlib.console',
              'gozerlib.gae',
              'gozerlib.gae.utils',
              'gozerlib.gae.web',
              'gozerlib.gae.wave',
              'gozerlib.gae.xmpp',
              'gozerlib.socklib',
              'gozerlib.socklib.irc',
              'gozerlib.socklib.xmpp',
              'gozerlib.socklib.utils',
              'gozerlib.socklib.rest',
              'gozerlib.contrib',
              'gozerlib.plugs',
              'waveplugs',
              'commonplugs',
              'socketplugs', 
              'gaeplugs'],
    package_dir={'jsonbot': ['gozerlib', 'waveplugs', 'commonplugs', 'socketplugs']},
    long_description = """ JSONBOT is a remote event-driven framework for building bots that talk JSON to each other over XMPP. IRC/Console/XMPP (shell) Wave/Web/XMPP (GAE) implementations provided. """,
    install_requires = ['simplejson>1.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: Other OS',
        'Programming Language :: Python',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
   zip_safe=False, 
   test_suite = 'nose.collector',
   data_files=[('gozerdata', uploadlist('gozerdata')),
               ('gozerdata' + os.sep + 'examples', uploadlist('gozerdata' + os.sep + 'examples')),
               ('gozerdata' + os.sep + 'myplugs', uploadlist('gozerdata' + os.sep + 'myplugs')),
               ('tests', uploadlist('tests')),
               ('simplejson', uploadlist('simplejson')),
               ('tweepy', uploadlist('tweepy')),
               ('gaeupload', uploadfiles('gaeupload')),
               ('gaeupload' + os.sep + 'webapp2', uploadlist('gaeupload' + os.sep + 'webapp2')),
               ('gaeupload' + os.sep + 'assets', uploadlist('gaeupload' + os.sep + 'assets')),
               ('gaeupload' + os.sep + 'templates', uploadlist('gaeupload' + os.sep +'templates')),
               ('gaeupload' + os.sep + 'waveapi', uploadlist('gaeupload' + os.sep + 'waveapi')),
               ('gaeupload' + os.sep + 'waveapi' + os.sep + 'oauth', uploadlist('gaeupload' + os.sep + 'waveapi' + os.sep + 'oauth')),
               ('gaeupload' + os.sep + 'waveapi' + os.sep + 'simplejson', uploadlist('gaeupload' + os.sep + 'waveapi' + os.sep + 'simplejson')),
               ('gaeupload' + os.sep + 'gadgets', uploadlist('gaeupload' + os.sep + 'gadgets'))],
)
