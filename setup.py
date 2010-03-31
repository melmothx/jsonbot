#!/usr/bin/env python
#
#

from setuptools import setup
import glob
import os

setup(
    name='jsonbot',
    version='0.1',
    url='http://jsonbot.googlecode.com/',
    download_url="http://code.google.com/p/jsonbot/downloads", 
    author='Bart Thate',
    author_email='bthate@gmail.com',
    description='The JSON everywhere bot ;] for wave/web/xmpp/IRC/console',
    license='MIT',
    scripts = ['bin/jsb', 
               'bin/jsb-boot',
               'bin/jsb-clone',
               'bin/jsb-irc',
               'bin/jsb-makedocs',
               'bin/jsb-makehtml',
               'bin/jsb-nose',
               'bin/jsb-release',
               'bin/jsb-run',
               'bin/jsb-runrelease',
               'bin/jsb-test',
               'bin/jsb-unittest',
               'bin/jsb-upload',
               'bin/jsb-uprelease'],
    packages=['gozerlib', 
              'gozerlib.utils', 
              'gozerlib.gae',
              'gozerlib.gae.utils',
              'gozerlib.gae.web',
              'gozerlib.gae.wave',
              'gozerlib.gae.xmpp',
              'gozerlib.socket',
              'gozerlib.socket.irc',
              'gozerlib.socket.util',
              'gozerlib.gozernet',
              'gozerlib.contrib',
              'gozerlib.plugs',
              'waveplugs',
              'commonplugs'],
    package_dir={'jsonbot': ['gozerlib', 'gozerlib.plugs', 'waveplugs', 'commonplugs']},
    install_requires = ['simplejson >= 1.0', 'nose >= 0.11'],
    long_description = """
JSONBOT is a bot that stores all its data in json format. It runs on the 
Google Application Engine and can thus support wave, web and xmpp. Standalone 
programms are provided for IRC and console, the goal is to let both clientside
and GAE side communicate through JSON either over XMPP or HTTP POST.
see http://jsonbot.googlecode.com
""",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Other Environment',
         'Framework :: GAE',
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
)
