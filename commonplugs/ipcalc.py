# IP subnet calculator
# (c) 2007 Wijnand 'tehmaze' Modderman - http://tehmaze.com
# BSD License

from gozerlib.commands import cmnds
from gozerlib.examples import examples

""" IP subnet calculator. this module allows you to perform network 
    calculations.
"""

"""
# IP subnet calculator
# (C) 2007 Wijnand 'tehmaze' Modderman - http://tehmaze.com
# BSD License
#
# ABOUT
#  This module allows you to perform network calculations.
#
# CHANGELOG
#  2007-10-26: Added IPv6 support, as well as a lot of other functions, 
#              refactored the calculations.
#  2007-10-25: Initial writeup, because I could not find any other workable
#              implementation.
#
# TODO
#  * add CLI parser
#
# REFERENCES
#  * http://www.estoile.com/links/ipv6.pdf
#  * http://www.iana.org/assignments/ipv4-address-space
#  * http://www.iana.org/assignments/multicast-addresses
#  * http://www.iana.org/assignments/ipv6-address-space
#  * http://www.iana.org/assignments/ipv6-tla-assignments
#  * http://www.iana.org/assignments/ipv6-multicast-addresses
#  * http://www.iana.org/assignments/ipv6-anycast-addresses
#
# THANKS (testing, tips)
#  * Bastiaan (trbs)
#  * Peter van Dijk (Habbie)
#  * Hans van Kranenburg (Knorrie)
#
"""

__version__ = '0.2a'

import types, socket

class IP(object):

    # Hex-to-Bin conversion masks
    _bitmask = {
        '0': '0000', '1': '0001', '2': '0010', '3': '0011',
        '4': '0100', '5': '0101', '6': '0110', '7': '0111',
        '8': '1000', '9': '1001', 'a': '1010', 'b': '1011',
        'c': '1100', 'd': '1101', 'e': '1110', 'f': '1111'
        }

    # IP range specific information, see IANA allocations.
    _range = {
        4: {
            '01'                    : 'CLASS A',
            '10'                    : 'CLASS B',
            '110'                   : 'CLASS C',
            '1110'                  : 'CLASS D MULTICAST',
            '11100000'              : 'CLASS D LINKLOCAL',
            '1111'                  : 'CLASS E',
            '00001010'              : 'PRIVATE RFC1918', # 10/8
            '101011000001'          : 'PRIVATE RFC1918', # 172.16/12
            '1100000010101000'      : 'PRIVATE RFC1918', # 192.168/16
            },
        6: {
            '00000000'              : 'RESERVED',       # ::/8
            '00000001'              : 'UNASSIGNED',     # 100::/8
            '0000001'               : 'NSAP',           # 200::/7
            '0000010'               : 'IPX',            # 400::/7
            '0000011'               : 'UNASSIGNED',     # 600::/7
            '00001'                 : 'UNASSIGNED',     # 800::/5
            '0001'                  : 'UNASSIGNED',     # 1000::/4
            '0010000000000000'      : 'RESERVED',       # 2000::/16 Reserved
            '0010000000000001'      : 'ASSIGNABLE',     # 2001::/16 Sub-TLA Assignments [RFC2450]
            '00100000000000010000000': 'ASSIGNABLE IANA',  # 2001:0000::/29 - 2001:01F8::/29 IANA
            '00100000000000010000001': 'ASSIGNABLE APNIC', # 2001:0200::/29 - 2001:03F8::/29 APNIC
            '00100000000000010000010': 'ASSIGNABLE ARIN',  # 2001:0400::/29 - 2001:05F8::/29 ARIN
            '00100000000000010000011': 'ASSIGNABLE RIPE',  # 2001:0600::/29 - 2001:07F8::/29 RIPE NCC
            '0010000000000010'      : '6TO4',           # 2002::/16 "6to4" [RFC3056]
            '0011111111111110'      : '6BONE TEST',     # 3ffe::/16 6bone Testing [RFC2471]
            '0011111111111111'      : 'RESERVED',  # 3fff::/16 Reserved
            '010'                   : 'GLOBAL-UNICAST', # 4000::/3
            '011'                   : 'UNASSIGNED',     # 6000::/3
            '100'                   : 'GEO-UNICAST',    # 8000::/3
            '101'                   : 'UNASSIGNED',     # a000::/3
            '110'                   : 'UNASSIGNED',     # c000::/3
            '1110'                  : 'UNASSIGNED',     # e000::/4
            '11110'                 : 'UNASSIGNED',     # f000::/5
            '111110'                : 'UNASSIGNED',     # f800::/6
            '1111110'               : 'UNASSIGNED',     # fc00::/7
            '111111100'             : 'UNASSIGNED',     # fe00::/9
            '1111111010'            : 'LINKLOCAL',      # fe80::/10
            '1111111011'            : 'SITELOCAL',      # fec0::/10
            '11111111'              : 'MULTICAST',      # ff00::/8
            '0' * 96                : 'IPV4COMP',       # ::/96
            '0' * 80 + '1' * 16     : 'IPV4MAP',        # ::ffff:0:0/96
            '0' * 128               : 'UNSPECIFIED',    # ::/128
            '0' * 127 + '1'         : 'LOOPBACK'        # ::1/128
            }
        }

    def __init__(self, ip, mask=None, version=0):
        self.mask = mask
        self.v = 0
        # Parse input
        if isinstance(ip, IP):
            self.ip = ip.ip
            self.dq = ip.dq
            self.v = ip.v
            self.mask = ip.mask
        elif type(ip) in [types.IntType, types.LongType]:
            self.ip = long(ip)
            if self.ip <= 0xffffffff:
                self.v = version or 4
                self.dq = self._itodq(ip)
            else:
                self.v = version or 4
                self.dq = self._itodq(ip)
        else:
            # If string is in CIDR notation
            if '/' in ip:
                ip, mask = ip.split('/', 1)
                self.mask = int(mask)
            self.v = version or 0
            self.dq = ip
            self.ip = self._dqtoi(ip)
            assert self.v != 0, 'Could not parse input'
        # Netmask defaults to one ip
        if self.mask is None:
            self.mask = self.v == 4 and 32 or 128
        # Validate subnet size
        if self.v == 6:
            self.dq = self._itodq(self.ip)
            if self.mask < 0 or self.mask > 128:
                raise ValueError, "IPv6 subnet size must be between 0 and 128"
        elif self.v == 4:
            if self.mask < 0 or self.mask > 32:
                raise ValueError, "IPv4 subnet size must be between 0 and 32"

    def bin(self):
        '''
        Full-length binary representation of the IP address.
        '''
        h = hex(self.ip).lower().rstrip('l')
        b = ''.join(self._bitmask[x] for x in h[2:])
        l = self.v == 4 and 32 or 128
        return ''.join('0' for x in xrange(len(b), l)) + b

    def hex(self):
        '''
        Full-length hexadecimal representation of the IP address.
        '''
        if self.v == 4:
            return '%08x' % self.ip
        else:
            return '%032x' % self.ip

    def subnet(self):
        return self.mask

    def version(self):
        return self.v
   
    def info(self):
        '''
        Show IANA allocation information for the current IP address.
        '''
        b = self.bin()
        l = self.v == 4 and 32 or 128
        for i in range(len(b), 0, -1):
            if self._range[self.v].has_key(b[:i]):
                return self._range[self.v][b[:i]]
        return 'UNKNOWN'
 
    def _dqtoi(self, dq):
        '''
        Convert dotquad or hextet to long.
        '''
        # hex notation
        if dq.startswith('0x'):
            ip = long(dq[2:], 16)
            if ip > 0xffffffffffffffffffffffffffffffffL:
                raise ValueError, "%r: IP address is bigger than 2^128" % dq
            if ip <= 0xffffffff:
                self.v = 4
            else:
                self.v = 6
            return ip

        # IPv6
        if ':' in dq:
            hx = dq.split(':') # split hextets
            if ':::' in dq:
                raise ValueError, "%r: IPv6 address can't contain :::" % dq
            # Mixed address (or 4-in-6), ::ffff:192.0.2.42
            if '.' in dq:
                return self._dqtoi(hx[-1])
            if len(hx) > 8:
                raise ValueError, "%r: IPv6 address with more than 8 hexletts" % dq
            elif len(hx) < 8:
                # No :: in address
                if not '' in hx:
                    raise ValueError, "%r: IPv6 address invalid: compressed format malformed" % dq
                elif not (dq.startswith('::') or dq.endswith('::')) and len([x for x in hx if x == '']) > 1:
                    raise ValueError, "%r: IPv6 address invalid: compressed format malformed" % dq
                ix = hx.index('')
                px = len(hx[ix+1:])
                for x in xrange(ix+px+1, 8):
                    hx.insert(ix, '0')
            elif dq.endswith('::'):
                pass
            elif '' in hx:
                raise ValueError, "%r: IPv6 address invalid: compressed format detected in full notation" % dq
            ip = ''
            hx = [x == '' and '0' or x for x in hx]
            for h in hx:
                if len(h) < 4:
                    h = '%04x' % int(h, 16)
                if 0 > int(h, 16) > 0xffff:
                    raise ValueError, "%r: IPv6 address invalid: hextets should be between 0x0000 and 0xffff" % dq
                ip += h
            self.v = 6
            return long(ip, 16)
        elif len(dq) == 32:
            # Assume full heximal notation
            self.v = 6
            return long(h, 16)
        
        # IPv4
        if '.' in dq:
            q = dq.split('.')
            if len(q) > 4:
                raise ValueError, "%r: IPv4 address invalid: more than 4 bytes" % dq
            for x in q:
                if 0 > int(x) > 255:
                    raise ValueError, "%r: IPv4 address invalid: bytes should be between 0 and 255" % dq
            self.v = 4
            return long(q[0])<<24 | long(q[1])<<16 | long(q[2])<<8 | long(q[3])
    
        raise ValueError, "Invalid address input"
       
    def _itodq(self, n):
        '''
        Convert long to dotquad or hextet.
        '''
        if self.v == 4:
            return '.'.join(map(str, [(n>>24) & 0xff, (n>>16) & 0xff, (n>>8) & 0xff, n & 0xff]))
        else:
            n = '%032x' % n
            return ':'.join(n[4*x:4*x+4] for x in xrange(0, 8))

    def __str__(self):
        return self.dq

    def __int__(self):
        return int(self.ip)

    def __long__(self):
        return self.ip

    def size(self):
        return 1

    def clone(self):
        '''
        Return a new <IP> object with a copy of this one.
        '''
        return IP(self)

    def to_ipv4(self):
        '''
        Convert (a IPv6) IP address to an IPv4 address, if possible. Only works
        for IPv4-compat (::/96) and 6-to-4 (2002::/16) addresses.
        '''
        if self.v == 4:
            return self
        else:
            if self.bin().startswith('0' * 96):
                return IP(long(self), version=4)
            elif long(self) & 0x20020000000000000000000000000000L:
                return IP((long(self)-0x20020000000000000000000000000000L)>>80, version=4)
            else:
                return ValueError, "%r: IPv6 address is not IPv4 compatible, nor a 6-to-4 IP" % self.dq

    def to_ipv6(self, type='6-to-4'):
        '''
        Convert (a IPv4) IP address to an IPv6 address.
        '''
        assert type in ['6-to-4', 'compat'], 'Conversion type not supported'
        if self.v == 4:
            if type == '6-to-4':
                return IP(0x20020000000000000000000000000000L | long(self)<<80, version=6)
            elif type == 'compat':
                return IP(long(self), version=6)
        else:
            return self

    def to_tuple(self):
        '''
        Used for comparisons.
        '''
        return (self.dq, self.mask)
    
class Network(IP):
    '''
    Network slice calculations.
    '''

    def netmask(self):
        '''
        Network netmask derived from subnet size.
        '''
        if self.version() == 4:
            return IP((0xffffffffL >> (32-self.mask)) << (32-self.mask), version=self.version())
        else:
            return IP((0xffffffffffffffffffffffffffffffffL >> (128-self.mask)) << (128-self.mask), version=self.version())

    def network(self):
        '''
        Network address.
        '''
        return IP(self.ip & long(self.netmask()), version=self.version())
    
    def broadcast(self):
        '''
        Broadcast address.
        '''
        # XXX: IPv6 doesn't have a broadcast address, but it's used for other 
        #      calculations such as <Network.host_last>.
        if self.version() == 4:
            return IP(long(self.network()) | (0xffffffff - long(self.netmask())), version=self.version())
        else:
            return IP(long(self.network()) | (0xffffffffffffffffffffffffffffffffL - long(self.netmask())), version=self.version())

    def host_first(self):
        '''
        First available host in this subnet.
        '''
        if (self.version() == 4 and self.mask == 32) or (self.version() == 6 and self.mask == 128):
            return self
        return IP(long(self.network())+1, version=self.version())

    def host_last(self):
        '''
        Last available host in this subnet.
        '''
        if (self.version() == 4 and self.mask == 32) or (self.version() == 6 and self.mask == 128):
            return self
        return IP(long(self.broadcast())-1, version=self.version())

    def in_network(self, other):
        '''
        Check if the given IP address is within this network.
        '''
        other = Network(other)
        return long(other) >= long(self) and long(other) < long(self) + self.size() - other.size() + 1

    def __contains__(self, ip):
        '''
        Check if the given ip is part of the network.

        >>> '192.0.2.42' in Network('192.0.2.0/24')
        True
        >>> '192.168.2.42' in Network('192.0.2.0/24')
        False
        '''
        return self.in_network(ip)

    def __lt__(self, other):
        return self.size() < IP(other).size()

    def __le__(self, other):
        return self.size() <= IP(other).size()

    def __gt__(self, other):
        return self.size() > IP(other).size()

    def __ge__(self, other):
        return self.size() >= IP(other).size()

    def __iter__(self):
        '''
        Generate a range of ip addresses within the network.

        >>> for ip in Network('192.168.114.0/30'): print str(ip)
        ... 
        192.168.114.0
        192.168.114.1
        192.168.114.2
        192.168.114.3
        '''
        for ip in [IP(long(self)+x) for x in xrange(0, self.size())]:
            yield ip

    def has_key(self, ip):
        '''
        Check if the given ip is part of the network.

        >>> net = Network('192.0.2.0/24')
        >>> net.has_key('192.168.2.0')
        False
        >>> net.has_key('192.0.2.42')
        True
        '''
        return self.__contains__(ip)

    def size(self):
        '''
        Number of ip's within the network.
        '''
        return 2 ** ((self.version() == 4 and 32 or 128) - self.mask)

def handle_ipcalc(bot, ievent):
    """ <ip>[</size>] .. calculate IP subnets. """
    if not ievent.args:
        ievent.missing('<ip>[/<size>]')
        return
    try:
        net = Network(ievent.args[0])
    except ValueError, e:
        ievent.reply('error: %s' % e)
        return
    ievent.reply('version: %d, address: %s, network size: %d, network address: %s, netmask: %s, first host in network: %s, last host in network: %s, network info: %s' % \
        (net.version(), str(net), net.mask, net.network(), net.netmask(), net.host_first(), net.host_last(), net.info()))

cmnds.add('ipcalc', handle_ipcalc, ['USER', 'GUEST'])
examples.add('ipcalc', 'ip calculator', 'ipcalc 127.0.0.1/12')
