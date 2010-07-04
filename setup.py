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
               'bin/jsb-upload'],
    packages=['gozerlib', 
              'gozerlib.utils', 
              'gozerlib.console',
              'gozerlib.gae',
              'gozerlib.gae.utils',
              'gozerlib.gae.web',
              'gozerlib.gae.wave',
              'gozerlib.gae.xmpp',
              'gozerlib.gae.plugs', 
              'gozerlib.socklib',
              'gozerlib.socklib.irc',
              'gozerlib.socklib.xmpp',
              'gozerlib.socklib.utils',
              'gozerlib.socklib.rest',
              'gozerlib.remote',
              'gozerlib.contrib',
              'gozerlib.plugs',
              'waveplugs',
              'commonplugs',
              'socketplugs'],
    package_dir={'jsonbot': ['gozerlib', 'waveplugs', 'commonplugs', 'socketplugs']},
    long_description = """ JSONBOT is a bot that stores all its data in json format. It runs on the Google Application Engine and can thus support wave, web and XMPP. Standalone programms are provided for IRC, XMPP and console. Both clientside and GAE side communicate through JSON either over XMPP. Relay IRC <-> Wave, XMPP <-> Wave, XMPP <-> IRC. """,
    install_requires = ['simplejson>1.0'],
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
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
   zip_safe=False, 
   test_suite = 'nose.collector',
   data_files=[('gozerdata', uploadlist('gozerdata')),
               ('gozerdata/myplugs', uploadlist('gozerdata/myplugs')),
               ('tests', uploadlist('tests')),
               ('simplejson', uploadlist('simplejson')),
               ('gaeupload', uploadlist('gaeupload')),
               ('gaeupload/assets', uploadlist('gaeupload/assets')),
               ('gaeupload/templates', uploadlist('gaeupload/templates')),
               ('gaeupload/waveapi', uploadlist('gaeupload/waveapi')),
               ('gaeupload/waveapi/oauth', uploadlist('gaeupload/waveapi/oauth')),
               ('gaeupload/gadgets', uploadlist('gaeupload/gadgets'))],
)
