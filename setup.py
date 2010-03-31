#!/usr/bin/env python
#
#

__copyright__ = 'this file is in the public domain'
__revision__ = '$Id: setup.py 71 2005-11-10 13:37:50Z bart $'

from setuptools import setup
import glob
import os

upload = []

def uploadlist(dir):
    upl = []
    
    for file in os.listdir(dir):
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
print upload

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
               'bin/jsb-installupload',
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
              'gozerlib.socket.utils',
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
   install_package_data=True,
   data_files=[('config', glob.glob('config/*.example') + ['config/__init__.py']),
               ('tests', glob.glob('tests/*.py') + ['tests/__init__.py']),
               ('gaeupload', glob.glob('gaeupload/*.py')),
               ('gaeupload/assets', uploadlist('gaeupload/assets')),
               ('gaeupload/templates', uploadlist('gaeupload/templates')),
               ('gaeupload/waveapi', uploadlist('gaeupload/waveapi')),
               ('gaeupload/gadgets', uploadlist('gaeupload/gadgets'))],
)
