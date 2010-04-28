# gozerlib/examples.py
#
#

""" examples is a dict of example objects. """

## basic imports

import re

class Example(object):

    """
        an example.

        :param descr: description of the example
        :type descr: string
        :param ex: the example
        :type ex: string

    """

    def __init__(self, descr, ex):
        self.descr = descr
        self.example = ex

class Examples(dict):

    """ examples holds all the examples. """

    def add(self, name, descr, ex):
        """
            add description and example.

            :param name: name of the example
            :type name: string
            :param descr: description of the example
            :type descr: string
            :param ex: the example
            :type ex: string

        """
        self[name.lower()] = Example(descr, ex)

    def size(self):
        """ return size of examples dict. """
        return len(self.keys())

    def getexamples(self):
        """ get all examples in list. """
        result = []
        for i in self.values():
            ex = i.example.lower()
            exampleslist = re.split('\d\)', ex)

            for example in exampleslist:
                if example:
                    result.append(example.strip())

        return result

# main examples object
examples = Examples()
