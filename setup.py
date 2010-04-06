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
    version='0.1.3',
    url='http://jsonbot.googlecode.com/',
    download_url="http://code.google.com/p/jsonbot/downloads", 
    author='Bart Thate',
    author_email='bthate@gmail.com',
    description='The JSON everywhere bot ;] for wave/web/xmpp/IRC/console',
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
              'gozerlib.gozernet',
              'gozerlib.contrib',
              'gozerlib.plugs',
              'waveplugs',
              'commonplugs'],
    package_dir={'jsonbot': ['gozerlib', 'waveplugs', 'commonplugs']},
    long_description = """
JSONBOT is a bot that stores all its data in json format. It runs on the 
Google Application Engine and can thus support wave, web and xmpp. Standalone 
programms are provided for IRC and console, the goal is to let both clientside
and GAE side communicate through JSON either over XMPP or HTTP POST.
see http://jsonbot.googlecode.com
""",
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
