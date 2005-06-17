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
import random

def random_bytes(length, choices=""):
    bytes = []
    if choices == "":
        for i in xrange(length):
            bytes.append(chr(random.randrange(0,256)))
    else:
        for i in xrange(length):
            bytes.append(random.choice(choices))
    return "".join(bytes)

class WormGen(object):
    def __init__(self, fname="filename", pname="Pretty Name"): pass

    def generate(self, count):
        """Generate 'count' samples of the worm"""
        raise NotImplementedError

    # indicates what ports a worm targets
    ports = property(lambda self: [])
