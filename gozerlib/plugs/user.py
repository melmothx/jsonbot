# gozerlib/plugs/user.py
#
#

""" users related commands. """

## gozerlib imports

from gozerlib.utils.generic import getwho
from gozerlib.utils.exception import handle_exception
from gozerlib.utils.name import stripname
from gozerlib.users import users
from gozerlib.commands import cmnds
from gozerlib.examples import examples

## basic imports

import logging

## commands

def handle_whoami(bot, ievent):
    """ get your username. """
    ievent.reply('%s' % bot.users.getname(ievent.auth))

cmnds.add('user-whoami', handle_whoami, ['USER', 'GUEST'])
examples.add('user-whoami', 'get your username', 'user-whoami')

def handle_meet(bot, ievent):
    """ <nick> .. introduce a new user to the bot. """
    try:
        nick = ievent.args[0]
    except IndexError:
        ievent.missing('<nick>')
        return

    if bot.users.exists(nick):
        ievent.reply('there is already a user with username %s' % nick)
        return

    userhost = getwho(bot, nick)
    logging.warn("users - meet - userhost is %s" % userhost)
    if not userhost:
        ievent.reply("can't find userhost of %s" % nick)
        return

    username = bot.users.getname(userhost)
    if username:
        ievent.reply('we already have a user with userhost %s (%s)' % \
(userhost, username))
        return

    result = 0
    name = stripname(nick.lower())
    result = bot.users.add(name, [userhost, ], ['USER', ])
    if result:
        ievent.reply('%s - %s - (%s) added to user database' % (nick, userhost, name))
    else:
        ievent.reply('add failed')

cmnds.add('user-meet', handle_meet, ['OPER', 'MEET'])
examples.add('user-meet', '<nick> .. introduce <nick> to the bot', 'user-meet dunker')

def handle_adduser(bot, ievent):
    """ user-add <name> <userhost> .. introduce a new user to the bot. """
    try:
        (name, userhost) = ievent.args
    except ValueError:
        ievent.missing('<name> <userhost>')
        return

    username = bot.users.getname(userhost)
    if username:
        ievent.reply('we already have a user with userhost %s (%s)' % (userhost, username))
        return

    result = 0
    name = stripname(name.lower()) 
    result = bot.users.add(name, [userhost, ], ['USER', ])
    if result:
        ievent.reply('%s added to user database' % name)
    else:
        ievent.reply('add failed')

cmnds.add('user-add', handle_adduser, 'OPER')
examples.add('user-add', '<name> <userhost> .. add <name> with \
<userhost> to the bot', 'user-add dunker bart@localhost')

def handle_merge(bot, ievent):
    """ <name> <nick> .. merge the userhost into a already existing user. """
    if len(ievent.args) != 2:
        ievent.missing('<name> <nick>')
        return

    name, nick = ievent.args
    name = name.lower()

    if bot.users.gotperm(name, 'OPER') and not bot.users.allowed(ievent.userhost, 'OPER'):
        ievent.reply("only OPER perm can merge with OPER user")
        return
    if name == 'owner' and not bot.ownercheck(ievent.userhost):
         ievent.reply("you are not the owner")
         return 
    if not bot.users.exists(name):
        ievent.reply("we have no user %s" % name)
        return
    userhost = getwho(bot, nick)
    if not userhost:
        ievent.reply("can't find userhost of %s" % nick)
        return
    if bot.ownercheck(userhost):
        ievent.reply("can't merge with owner")
        return
    username = bot.users.getname(userhost)
    if username:
        ievent.reply('we already have a user with userhost %s (%s)' % (userhost, username))
        return

    result = bot.users.merge(name, userhost)
    if result:
        ievent.reply('%s merged' % nick)
    else:
        ievent.reply('merge failed')

cmnds.add('user-merge', handle_merge, ['OPER', 'MEET'])
examples.add('user-merge', '<name> <nick> .. merge record with <name> with userhost from <nick>', 'user-merge bart dunker')

def handle_import(bot, ievent):
    """ user-import <userhost> .. merge the userhost into user giving the command. """
    if len(ievent.args) != 1:
        ievent.missing('<userhost>')
        return

    userhost = ievent.args[0]

    if bot.ownercheck(userhost):
        ievent.reply("can't merge owner")
        return

    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("i don't know you %s" % ievent.userhost)
        return

    result = bot.users.merge(name, userhost)
    if result:
        ievent.reply('%s imported' % userhost)
    else:
        ievent.reply('import failed')

cmnds.add('user-import', handle_import, ['IMPORT', 'OPER'])
examples.add('user-import', 'user-import <userhost> .. merge record with \
<name> with userhost from the person giving the command (self merge)', 'user-import bthate@gmail.com')

def handle_delete(bot, ievent):
    """ <name> .. remove user. """
    if not bot.ownercheck(ievent.userhost):
        ievent.reply('only owner can use delete')
        return
    if len(ievent.args) == 0:
        ievent.missing('<name>')
        return

    name = ievent.args[0].lower()
    result = 0
    name = stripname(name.lower())
    name = name.lower()
    try:
        result = bot.users.delete(name)
        if result:
            ievent.reply('%s deleted' % name)
            return
    except KeyError:
        pass

    ievent.reply('no %s item in database' % name)

cmnds.add('user-del', handle_delete, 'OPER')
examples.add('user-del', 'user-del <name> .. delete user with <username>' , 'user-del dunker')

def handle_userscan(bot, ievent):
    """ <txt> .. scan for user. """
    try:
        name = ievent.args[0]
    except IndexError:
        ievent.missing('<txt>')
        return

    name = name.lower()
    names = bot.users.names()
    result = []
    for i in names:
        if i.find(name) != -1:
            result.append(i)

    if result:
        ievent.reply("users matching %s: " % name, result)
    else:
        ievent.reply('no users matched')
        return

cmnds.add('user-scan', handle_userscan, 'OPER')
examples.add('user-scan', '<txt> .. search database for matching usernames', 'user-scan dunk')

def handle_names(bot, ievent):
    """ show registered users. """
    ievent.reply("usernames: ", bot.users.names())

cmnds.add('user-names', handle_names, 'OPER')
examples.add('user-names', 'show names of registered users', 'user-names')

def handle_name(bot, ievent):
    """ user-name .. show name of user giving the command. """
    ievent.reply('your name is %s' % bot.users.getname(ievent.userhost))

cmnds.add('user-name', handle_name, ['USER', 'GUEST'])
examples.add('user-name', 'show name of user giving the commands', 'user-name')

def handle_getname(bot, ievent):
    """ <nick> .. fetch username of nick. """
    try:
        nick = ievent.args[0]
    except IndexError:
        ievent.missing("<nick>")
        return

    userhost = getwho(bot, nick)
    if not userhost:
        ievent.reply("can't find userhost of %s" % nick)
        return

    name = bot.users.getname(userhost)
    if not name:
        ievent.reply("can't find user for %s" % userhost)
        return

    ievent.reply(name)

cmnds.add('user-getname', handle_getname, ['USER', ])
examples.add('user-getname', 'user-getname <nick> .. get the name of <nick>', 'user-getname dunker')

def handle_addperm(bot, ievent):
    """ <name> <perm> .. add permission. """
    if len(ievent.args) != 2:
        ievent.missing('<name> <perm>')
        return

    name, perm = ievent.args
    perm = perm.upper()
    name = name.lower()
    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return

    result = 0
    if bot.users.gotperm(name, perm):
        ievent.reply('%s already has permission %s' % (name, perm))
        return         

    result = bot.users.adduserperm(name, perm)
    if result:
        ievent.reply('%s perm added' % perm)
    else:
        ievent.reply('perm add failed')

cmnds.add('user-addperm', handle_addperm, 'OPER')
examples.add('user-addperm', 'user-addperm <name> <perm> .. add permissions to user <name>', 'user-addperm dunker rss')

def handle_getperms(bot, ievent):
    """ <name> .. get permissions of name. """
    try:
        name = ievent.args[0]
    except IndexError:
        ievent.missing('<name>')
        return

    name = name.lower()
    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return

    perms = bot.users.getuserperms(name)
    if perms:
        ievent.reply("permissions of %s: " % name, perms)
    else:
        ievent.reply('%s has no permissions set' % name)

cmnds.add('user-getperms', handle_getperms, 'OPER')
examples.add('user-getperms', 'user-getperms <name> .. get permissions of <name>', 'user-getperms dunker')

def handle_perms(bot, ievent):
    """ get permissions of the user given the command. """
    if ievent.rest:
        ievent.reply("use getperms to get the permissions of somebody else")
        return

    name = bot.users.getname(ievent.userhost)
    if not name:
         ievent.reply("can't find username for %s" % ievent.userhost)
         return

    perms = bot.users.getuserperms(name)
    if perms:
        ievent.reply("you have permissions: ", perms)

cmnds.add('user-perms', handle_perms, ['USER', 'GUEST'])
examples.add('user-perms', 'get permissions', 'user-perms')

def handle_delperm(bot, ievent):
    """ <name> <perm> .. delete permission. """
    if len(ievent.args) != 2:
        ievent.missing('<name> <perm>')
        return

    name, perm = ievent.args
    perm = perm.upper()
    name = name.lower()
    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return

    result = bot.users.deluserperm(name, perm)
    if result:
        ievent.reply('%s perm removed' % perm)
    else:
        ievent.reply("%s has no %s permission" % (name, perm))
        return

cmnds.add('user-delperm', handle_delperm, 'OPER')
examples.add('user-delperm', 'delete from user <name> permission <perm>', 'user-delperm dunker rss')

def handle_addstatus(bot, ievent):
    """ <name> <status> .. add status of name. """
    if len(ievent.args) != 2:
        ievent.missing('<name> <status>')
        return

    name, status = ievent.args
    status = status.upper()
    name = name.lower()
    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return
    if bot.users.gotstatus(name, status):
        ievent.reply('%s already has status %s' % (name, status))
        return

    result = bot.users.adduserstatus(name, status)
    if result:
        ievent.reply('%s status added' % status)
    else:
        ievent.reply('add failed')

cmnds.add('user-addstatus', handle_addstatus, 'OPER')
examples.add('user-addstatus', 'user-addstatus <name> <status>', 'user-addstatus dunker #dunkbots')

def handle_getstatus(bot, ievent):
    """ <name> .. get status of name. """
    try:
        name = ievent.args[0]
    except IndexError:
        ievent.missing('<name>')
        return

    name = name.lower()
    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return

    status = bot.users.getuserstatuses(name)
    if status:
        ievent.reply("status of %s: " % name, status)
    else:
        ievent.reply('%s has no status set' % name)

cmnds.add('user-getstatus', handle_getstatus, 'OPER')
examples.add('user-getstatus', 'user-getstatus <name> .. get status of <name>', 'user-getstatus dunker')

def handle_status(bot, ievent):
    """ get status of user given the command. """
    status = bot.users.getstatuses(ievent.userhost)
    if status:
        ievent.reply("you have status: ", status)
    else:
        ievent.reply('you have no status set')

cmnds.add('user-status', handle_status, ['USER', 'GUEST'])
examples.add('user-status', 'get status', 'user-status')

def handle_delstatus(bot, ievent):
    """ <name> <status> .. delete status. """
    if len(ievent.args) != 2:
        ievent.missing('<name> <status>')
        return

    name, status = ievent.args
    status = status.upper()
    name = name.lower()

    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return

    result = bot.users.deluserstatus(name, status)

    if result:
        ievent.reply('%s status deleted' % status)
    else:
        ievent.reply("%s has no %s status" % (name, status))
        return

cmnds.add('user-delstatus', handle_delstatus, 'OPER')
examples.add('user-delstatus', '<name> <status>', 'user-delstatus dunker #dunkbots')

def handle_adduserhost(bot, ievent):
    """ <name> <userhost> .. add to userhosts of name. """ 
    if len(ievent.args) != 2:
        ievent.missing('<name> <userhost>')
        return

    name, userhost = ievent.args
    name = name.lower()
    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return
    if bot.users.gotuserhost(name, userhost):
        ievent.reply('%s already has userhost %s' % (name, userhost))
        return

    result = bot.users.adduserhost(name, userhost)
    if result:
        ievent.reply('userhost added')
    else:
        ievent.reply('add failed')

cmnds.add('user-adduserhost', handle_adduserhost, 'OPER')
examples.add('user-adduserhost', 'user-adduserhost <name> <userhost>', 'user-adduserhost dunker bart@%.a2000.nl')

def handle_deluserhost(bot, ievent):
    """ <name> <userhost> .. remove from userhosts of name. """
    if len(ievent.args) != 2:
        ievent.missing('<name> <userhost>')
        return

    name, userhost = ievent.args
    name = name.lower()
    if bot.ownercheck(userhost):
        ievent.reply('can delete userhosts from owner')
        return
    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return

    result = bot.users.deluserhost(name, userhost)
    if result:
        ievent.reply('userhost removed')
    else:
        ievent.reply("%s has no %s in userhost list" % (name, userhost))
        return  

cmnds.add('user-deluserhost', handle_deluserhost, 'OPER')
examples.add('user-deluserhost', 'user-deluserhost <name> <userhost> .. delete from usershosts of <name> userhost <userhost>','user-deluserhost dunker bart1@bla.a2000.nl')

def handle_getuserhosts(bot, ievent):
    """ <name> .. get userhosts. """
    try:
        who = ievent.args[0]
    except IndexError:
        ievent.missing('<name>')
        return

    who = who.lower()
    userhosts = bot.users.getuserhosts(who)
    if userhosts:
        ievent.reply("userhosts of %s: " % who, userhosts)
    else:
        ievent.reply("can't find user %s" % who)

cmnds.add('user-getuserhosts', handle_getuserhosts, 'OPER')
examples.add('user-getuserhosts', 'user-getuserhosts <name> .. get userhosts of <name>', 'user-getuserhosts dunker')

def handle_userhosts(bot, ievent):
    """ get userhosts of user giving the command. """
    userhosts = bot.users.gethosts(ievent.userhost)
    if userhosts:
        ievent.reply("you have userhosts: ", userhosts)

cmnds.add('user-userhosts', handle_userhosts, ['USER', 'GUEST'])
examples.add('user-userhosts', 'get userhosts', 'user-userhosts')

def handle_getemail(bot, ievent):
    """ <name> .. get email addres. """
    try:
        name = ievent.args[0]
    except IndexError:
        ievent.missing('<name>')
        return
    name = name.lower()
    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return

    email = bot.users.getuseremail(name)
    if email:
        ievent.reply(email)
    else:
        ievent.reply('no email set')

cmnds.add('user-getemail', handle_getemail, ['USER', ])
examples.add('user-getemail', 'user-getemail <name> .. get email from user <name>', 'user-getemail dunker')

def handle_setemail(bot, ievent):
    """ <name> <email> .. set email. """
    try:
        name, email = ievent.args
    except ValueError:
        ievent.missing('<name> <email>')
        return

    if not bot.users.exists(name):
        ievent.reply("can't find user %s" % name)
        return

    bot.users.setemail(name, email)
    ievent.reply('email set')

cmnds.add('user-setemail', handle_setemail, 'OPER')
examples.add('user-setemail', 'user-setemail <name> <email>.. set email of user <name>', 'user-setemail dunker bart@gozerbot.org')

def handle_email(bot, ievent):
    """ show email of user giving the command. """
    if len(ievent.args) != 0:
        ievent.reply('use getemail to get the email address of an user .. email shows your own mail address')
        return

    email = bot.users.getemail(ievent.userhost)
    if email:
        ievent.reply(email)
    else:
        ievent.reply('no email set')

cmnds.add('user-email', handle_email, ['USER', 'GUEST'])
examples.add('user-email', 'get email', 'user-email')

def handle_delemail(bot, ievent):
    """ reset email of user giving the command. """
    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find user for %s" % ievent.userhost)
        return

    result = bot.users.delallemail(name)
    if result:
        ievent.reply('email removed')
    else:
        ievent.reply('delete failed')

cmnds.add('user-delemail', handle_delemail, 'OPER')
examples.add('user-delemail', 'reset email', 'user-delemail')

def handle_addpermit(bot, ievent):
    """ <name> <permit> .. add permit to permit list of <name>. """
    try:
        who, what = ievent.args
    except ValueError:
        ievent.missing("<name> <permit>")
        return
    if not bot.users.exists(who):
        ievent.reply("can't find username of %s" % who)
        return

    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("i dont know %s" % ievent.userhost)
        return
    if bot.users.gotpermit(name, (who, what)):
        ievent.reply('%s is already allowed to do %s' % (who, what))
        return

    result = bot.users.adduserpermit(name, who, what)
    if result:
        ievent.reply('permit added')
    else:
        ievent.reply('add failed')

cmnds.add('user-addpermit', handle_addpermit, ['USER', 'GUEST'])
examples.add('user-addpermit', 'user-addpermit <nick> <what> .. permit nick access to <what> .. use setperms to add permissions', 'user-addpermit dunker todo')

def handle_permit(bot, ievent):
    """ get permit list of user giving the command. """
    if ievent.rest:
        ievent.reply("use the user-addpermit command to allow somebody something .. use getname <nick> to get the username of somebody .. this command shows what permits you have")
        return

    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("can't find user for %s" % ievent.userhost)
        return

    permits = bot.users.getuserpermits(name)
    if permits:
        ievent.reply("you permit the following: ", permits)
    else:
        ievent.reply("you don't have any permits")

cmnds.add('user-permit', handle_permit, ['USER', 'GUEST'])
examples.add('user-permit', 'show permit of user giving the command', 'user-permit')

def handle_userdelpermit(bot, ievent):
    """ <name> <permit> .. remove (name, permit) from permit list. """
    try:
        who, what = ievent.args
    except ValueError:
        ievent.missing("<name> <permit>")
        return

    if not bot.users.exists(who):
        ievent.reply("can't find registered name of %s" % who)
        return

    name = bot.users.getname(ievent.userhost)
    if not name:
        ievent.reply("i don't know you %s" % ievent.userhost)
        return
    if not bot.users.gotpermit(name, (who, what)):
        ievent.reply('%s is already not allowed to do %s' % (who, what))
        return

    result = bot.users.deluserpermit(name, (who, what))
    if result:
        ievent.reply('%s denied' % what)
    else:
        ievent.reply('delete failed')

cmnds.add('user-delpermit', handle_userdelpermit, ['USER', 'GUEST'])
examples.add('user-delpermit', 'user-delpermit <name> <permit>', 'user-delpermit dunker todo')

def handle_check(bot, ievent):
    """ <nick> .. get user data of <nick>. """
    try:
        nick = ievent.args[0]
    except IndexError:
        ievent.missing('<nick>')
        return

    userhost = getwho(bot, nick)
    if not userhost:
        ievent.reply("can't find userhost of %s" % nick)
        return

    name = bot.users.getname(userhost)
    if not name:
        ievent.reply("can't find user")
        return

    userhosts = bot.users.getuserhosts(name)
    perms = bot.users.getuserperms(name)
    email = bot.users.getuseremail(name)
    permits = bot.users.getuserpermits(name)
    status = bot.users.getuserstatuses(name)
    ievent.reply('userrecord of %s = userhosts: %s perms: %s email: %s permits: %s status: %s' % (name, str(userhosts), str(perms), str(email), str(permits), str(status)))

cmnds.add('user-check', handle_check, 'OPER')
examples.add('user-check', 'user-check <nick>', 'user-check dunker')

def handle_show(bot, ievent):
    """ <name> .. get user data of <name>. """
    try:
        name = ievent.args[0]
    except IndexError:
        ievent.missing('<name>')
        return

    name = name.lower()
    user = bot.users.byname(name) 

    if not user:
        ievent.reply("can't find user %s" % name)
        return

    userhosts = str(user.data.userhosts)
    perms = str(user.data.perms)
    email = str(user.data.email)
    permits = str(user.data.permits)
    status = str(user.data.status)
    ievent.reply('userrecord of %s = userhosts: %s perms: %s email: %s permits: %s status: %s' % (name, userhosts, perms, email, permits, status))

cmnds.add('user-show', handle_show, 'OPER')
examples.add('user-show', 'user-show <name> .. show data of <name>', 'user-show dunker')

def handle_match(bot, ievent):
    """ user-match <userhost> .. get data of <userhost>. """
    try:
        userhost = ievent.args[0]
    except IndexError:
        ievent.missing('<userhost>')
        return

    user = bot.users.getuser(userhost)
    if not user:
        ievent.reply("can't find user with userhost %s" % userhost)
        return

    userhosts = str(user.data.userhosts)
    perms = str(user.data.perms)
    email = str(user.data.email)
    permits = str(user.data.permits)
    status = str(user.data.status)
    ievent.reply('userrecord of %s = userhosts: %s perms: %s email: %s permits: %s status: %s' % (userhost, userhosts, perms, email, permits, status))

cmnds.add('user-match', handle_match, ['OPER', ])
examples.add('user-match', 'user-match <userhost>', 'user-match test@test')

def handle_getuserstatus(bot, ievent):
    """ <status> .. list users with status <status>. """
    try:
        status = ievent.args[0].upper()
    except IndexError:
        ievent.missing('<status>')
        return

    result = bot.users.getstatususers(status)
    if result:
        ievent.reply("users with %s status: " % status, result)
    else:
        ievent.reply("no users with %s status found" % status)
    return

cmnds.add('user-allstatus', handle_getuserstatus, 'OPER')
examples.add('user-allstatus', 'user-allstatus <status> .. get all users with <status> status', 'user-allstatus #dunkbots')

def handle_getuserperm(bot, ievent):
    """ <perm> .. list users with permission <perm>. """
    try:
        perm = ievent.args[0].upper()
    except IndexError:
        ievent.missing('<perm>')
        return

    result = bot.users.getpermusers(perm)

    if result:
        ievent.reply('users with %s permission: ' % perm, result)
    else:
        ievent.reply("no users with %s permission found" % perm)
    return

cmnds.add('user-allperm', handle_getuserperm, 'OPER')
examples.add('user-allperm', 'user-allperm <perm> .. get users with <perm> permission', 'user-allperm rss')

def handle_usersearch(bot, ievent):
    """ <txt> .. search for user matching given userhost. """
    try:
        what = ievent.args[0]
    except IndexError:
        ievent.missing('<txt>')
        return

    result = bot.users.usersearch(what)
    if result:
        res = ["(%s) %s" % u for u in result]
        ievent.reply('users matching %s: ' % what, res)
    else:
        ievent.reply('no userhost matching %s found' % what)

cmnds.add('user-search', handle_usersearch, 'OPER')
examples.add('user-search', 'search users userhosts', 'user-search gozerbot')

def handle_addpermall(bot, ievent):
    """ <perm> .. add permission to all users. """
    try:
        perm = ievent.args[0].upper()
    except IndexError:
        ievent.missing('<perm>')
        return

    if perm == 'OPER':
        ievent.reply("can't add OPER permissions to all")
        return

    bot.users.addpermall(perm)
    ievent.reply('%s perm added' % perm)

#cmnds.add('user-addpermall', handle_addpermall, 'OPER')
#examples.add('user-addpermall', 'user-addpermall <perm> .. add <permission> to all users', 'addpermsall USER')

def handle_delpermall(bot, ievent):
    """ <perm> .. delete permission from all users. """
    try:
        perm = ievent.args[0].upper()
    except IndexError:
        ievent.missing('<perm>')
        return

    if perm == 'OPER':
        ievent.reply("can't delete OPER permissions from all")
        return

    bot.users.delpermall(perm)
    ievent.reply('%s perm deleted' % perm)

#cmnds.add('user-delpermall', handle_delpermall, 'OPER')
#examples.add('user-delpermall', 'user-delpermall <perm> .. delete <permission> from all users', 'delpermsall BLA')
