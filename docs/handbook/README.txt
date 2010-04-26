README
======

JSONBOT is a bot that stores all its data in json format. It runs on the
Google Application Engine and can thus support wave, web and xmpp.
Standalone programms are provided for IRC and console, the goal is to let both
clientside and GAE side communicate through JSON either over XMPP or HTTP POST.

* Live demo: http://jsonbot.appspot.com (web) 
* Wave/Jabber: jsonbot@appspot.com

this bot needs google_appengine installed in your home dir

jsonbot provides the following programs:

* jsb - console version of jsonbot
* jsb-irc - IRC version of jsonbot
* jsb-release - create a new release directory
* jsb-run - run a release in the GAE dev_appserver
* jsb-upload - upload a release to the GAE

see docs/UPLOAD on how to upload your own bot.

running a development version of the bot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

first checkout the main bot from the mercurial repository

``hg clone http://jsonbot.googlecode.com/hg``

now you can run the programs in the bin directory with the ``./bin/<program>``  command. try ./bin/fpr for the console app


contact the developer
~~~~~~~~~~~~~~~~~~~~~

* email: bthate@gmail.com
* preview: bthate@googlewave.com
* sandbox: bthate@wavesandbox.com

You can reach me by joining #dunkbots on FreeNode or IRCNet. If we are not online on irc please email bthate@gmail.com if you have any problems with the bot.

JSONBOT is free open source code (MIT).
