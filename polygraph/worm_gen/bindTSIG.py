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

class bindTSIG(worm_gen.WormGen):
    def __init__(self, fname="tsig", 
                pname="Bind TSIG"): 
        self.pname = pname
        self.fname = fname

    def generate(self, count):
        for i in xrange(count):
            request = []
            bytes = [chr(i) for i in xrange(256)]

            # DNS ID
            request.append(random_bytes(2, bytes))

            # first bit is 0 to indicate a query.
            byte = random.choice(range(256))
            byte &= ~(0x80)
            request.append(chr(byte))

            # randomly choose 'recursion not available' bit
            # all other bits should be zero, but not checked
            # by server
#            request.append(random.choice(['\x80', '\x00']))
            request.append(random_bytes(2, bytes))

            # number of entries in question section. 2 in published exploit.
            # chosen randomly here.
            # realistically, it can probably only be a relatively small
            # number though.
            request.append(random_bytes(2, bytes))

            # resource records in the answer section
            request.append(random_bytes(2, bytes))

            # ns resource records in the authority answer section
            request.append(random_bytes(2, bytes))

            # resource records in additional record section 
            # anything but zero
            request.append(struct.pack('H', random.choice(xrange(1,2**16))))

            # first encoded QNAME (shell code)
            # technically this needs to be properly encoded. 
            # i.e., a byte indicating length, that many bytes, another byte
            # indicating length, etc. For signature
            # generation purposes though, it might as well be random bytes.
            request.append(random_bytes(256, bytes))
            
            # could be all one QNAME instead of two
#            request.append(chr(0))

            # apparently server doesn't check this value, 
            # so it could actually vary
#            request.append(chr(0) + chr(1) + chr(0) + chr(1))
            request.append(random_bytes(4, bytes))

            # second encoded QNAME (part is used as stack frame after overwrite)
            request.append(random_bytes(62, bytes))
            
            # Hyang-Ah has seen versions without this.
#            request.append(chr(6) + chr(0) + chr(0) +chr(0))

            # two stack addresses. more in actual exploit, 
            # but may not be necessary.
            # update- Hyang-Ah thinks only one...
            request.append(random_bytes(2, bytes))
#            request.append('\xff\xbf')
            request.append(random_bytes(2, bytes))
            request.append('\xff\xbf')

            # the rest of the second QNAME
            request.append(random_bytes(200, bytes))
            request.append(chr(0))

            # apparently server doesn't check this value, 
            # so it could actually vary
#            request.append(chr(0) + chr(1) + chr(0) + chr(1))
            request.append(random_bytes(4, bytes))

            # another encoded field ending with 00. 
            # has 0 length in actual exploit
            request.append(random_bytes(10, bytes))
            request.append(chr(0))

            # record type. FIXED 
            request.append(chr(0) + chr(0xfa))
            
            # record class. should be 0x00ff, but not checked by server
            request.append(random_bytes(2, bytes))

            yield ''.join(request)

    ports = property(lambda self: [53])
