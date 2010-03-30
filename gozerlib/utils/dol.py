# gozerbot/dol.py
#
#

""" dict of lists """

__copyright__ = 'this file is in the public domain'

class Dol(dict):

    """ dol is dict of lists """

    def insert(self, nr, item, issue):
        """ add issue to item entry """
        if self.has_key(item):
            self[item].insert(nr, issue)
        else:
            self[item] = [issue]
        return 1

    def add(self, item, issue):
        """ add issue to item entry """
        if self.has_key(item):
            self[item].append(issue)
        else:
            self[item] = [issue]
        return 1

    def adduniq(self, item, issue):
        """ only add issue to item if it is not already there """
        if self.has_key(item):
            if issue in self[item]:
                return 0
        self.add(item, issue)
        return 1
            
    def delete(self, item, number):
        """ del self[item][number] """
        number = int(number)
        if self.has_key(item):
            try:
                del self[item][number]
                return 1
            except IndexError:
                return None

    def remove(self, item, issue):
        """ remove issue from item """
        try:
            self[item].remove(issue)
            return 1
        except ValueError:
            pass

    def has(self, item, issue):
        """ check if item has issue """
        try:
            if issue in self[item]:
                return 1
            else:
                return None
        except KeyError:
            pass
