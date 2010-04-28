# gozerlib/utils/web.py
#
#

""" web related functions. """

## gozerlib imports

from gozerlib.utils.generic import fromenc, getversion

## gaelib imports

from auth import finduser

## google imports

from google.appengine.api import users as gusers
from google.appengine.ext.webapp import template

## basic imports

import os
import time

## functions

def mini(response, input={}):
    """ display start html so that bot output can follow. """
    inputdict = {'version': getversion()}
    if input:
        inputdict.update(input)
    temp = os.path.join(os.getcwd(), 'templates/mini.html')
    outstr = template.render(temp, inputdict)
    response.out.write(outstr)

def start(response, input={}):
    """ display start html so that bot output can follow. """
    inputdict = {'version': getversion()}
    if input:
        inputdict.update(input)
    temp = os.path.join(os.getcwd(), 'templates/start.html')
    outstr = template.render(temp, inputdict)
    response.out.write(outstr)

def commandbox(response, url="/dispatch/"):
    """ write html data for the exec box. """
    response.out.write("""
          <form action="%s" method="post">
            <div><b>enter command:</b> <input type="commit" name="content"></div>
          </form>
          """ % url)

def execbox(response, url="/exec/"):
    """ write html data for the exec box. """
    response.out.write("""
      <form action="" method="GET">
        <b>enter command:</b><input type="commit" name="input" value="">
        // <input type="button" value="go" onClick="makePOSTRequest(this.form)"
      </form>
          """)

def closer(response):
    """ send closing html .. comes after the bot output. """
    response.out.write('</div><div class="footer">')
    response.out.write('<b>%4f seconds</b></div>' % (time.time() - response.starttime))
    response.out.write('</body></html>')

def loginurl(response):
    """ return google login url. """
    return gusers.create_login_url("/")

def logouturl(response):
    """ return google login url. """
    return gusers.create_logout_url("/")
