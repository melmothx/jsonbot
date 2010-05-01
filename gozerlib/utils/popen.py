# gozerlib/utils/popen.py
#
#

""" popen helper functions """

go = False

try:
    from subprocess import Popen, PIPE
    from locking import lockdec
    import thread, StringIO, logging, types
    go = True
except:
    go = False

if go:
    popenlock = thread.allocate_lock()
    popenlocked = lockdec(popenlock)

    class PopenWhitelistError(Exception):

        def __init__(self, item):
            Exception.__init__(self)
            self.item = item
        
        def __str__(self):
            return self.item

    class PopenListError(Exception):

        def __init__(self, item):
            Exception.__init__(self)
            self.item = item
        
        def __str__(self):
            return str(self.item)

    class GozerStringIO(StringIO.StringIO):

        def readlines(self):
            return self.read().split('\n')

    class Gozerpopen4(Popen):

        def __init__(self, args):
            Popen.__init__(self, args, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
            self.fromchild = self.stdout
            self.tochild   = self.stdin
            self.errors    = self.stderr

        def close(self):
            self.wait()
            try:
                self.stdin.close()
            except:
                pass
            try:
                self.stdout.close()
            except:
                pass
            try:
                self.errors.close()
            except:
                pass
            return self.returncode

    def gozerpopen(args, userargs=[]):

        if type(args) != types.ListType:
            raise PopenListError(args)

        if type(userargs) != types.ListType:
            raise PopenListError(args)

        for i in userargs:
            if i.startswith('-'):
                raise PopenWhitelistError(i)

        proces = Gozerpopen4(args + userargs)
        return proces
