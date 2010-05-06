# gozerlib/socket/xmpp/JID.py
#
#

## classes

class InvalidJID(BaseException):

    pass

class JID(object):

    def __init__(self, str):
        if not str:
            self.full = ""
            self.user = ""
            self.userhost = ""
            self.host = ""
            self.resource = ""
            return
        if not self.validate(str):
            raise InvalidJID(str)
        self.full = str
        self.user = self.full.split('@')[0]
        self.userhost = self.full.split('/')[0]
        try:
             self.host = self.userhost.split('@')[1]
        except (IndexError, ValueError):
            raise InvalidJID(str)
            
        try:
            self.resource = self.full.split('/')[1]
        except (IndexError, ValueError):
            self.resource = u""

    def validate(self, s):
        if not '#' in s:
            return True
