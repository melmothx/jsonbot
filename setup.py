#!/usr/bin/env python
#
#

from setuptools import setup
import glob
import os

upload = []

def uploadlist(dir):
    upl = []
    
    for file in os.listdir(dir):
        if not file or file.startswith('.'):
            continue
        d = dir + os.sep + file
        if os.path.isdir(d):
            #upload.append(dir + os.sep + file)
            upl.extend(uploadlist(d))
        else:
            if file.endswith(".pyc"):
                continue
            upl.append(d)   

    return upl

upload = uploadlist('gaeupload')

setup(
    name='jsonbot',
    version='0.2',
    url='http://jsonbot.googlecode.com/',
    download_url="http://code.google.com/p/jsonbot/downloads", 
    author='Bart Thate',
    author_email='bthate@gmail.com',
    description='The JSON everywhere bot!',
    license='MIT',
    scripts = ['bin/jsb', 
               'bin/jsb-irc', 
               'bin/jsb-release',
               'bin/jsb-run',
               'bin/jsb-upload'],
    packages=['gozerlib', 
              'gozerlib.utils', 
              'gozerlib.gae',
              'gozerlib.gae.utils',
              'gozerlib.gae.web',
              'gozerlib.gae.wave',
              'gozerlib.gae.xmpp',
              'gozerlib.socket',
              'gozerlib.socket.irc',
              'gozerlib.socket.utils',
              'gozerlib.socket.rest',
              'gozerlib.remote',
              'gozerlib.contrib',
              'gozerlib.plugs',
              'waveplugs',
              'commonplugs',
              'socketplugs'],
    package_dir={'jsonbot': ['gozerlib', 'waveplugs', 'commonplugs', 'socketplugs']},
    long_description = """ JSONBOT is a wave and xmpp bot for pushing pubsubhubbub feeds to Google Wave and Jabber (see jsonbot@appspot.com). Combined with a feed fetching service like superfeedr.com it can deliver your feeds on multiple platforms (wave and xmpp are suported now though xmpp conferences aren't yet) - JSONBOT runs on the Google Application Engine - IRC support is on its way. """,
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
   data_files=[('config', uploadlist('config')),
               ('tests', uploadlist('tests')),
               ('simplejson', uploadlist('simplejson')),
               ('gaeupload', uploadlist('gaeupload')),
               ('gaeupload/assets', uploadlist('gaeupload/assets')),
               ('gaeupload/templates', uploadlist('gaeupload/templates')),
               ('gaeupload/waveapi', uploadlist('gaeupload/waveapi')),
               ('gaeupload/waveapi/oauth', uploadlist('gaeupload/waveapi/oauth')),
               ('gaeupload/gadgets', uploadlist('gaeupload/gadgets'))],
)
