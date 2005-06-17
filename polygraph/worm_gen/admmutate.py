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
import os

class ADMmutate(worm_gen.WormGen):
    def __init__(self, fname="ADMmutate", 
                pname="ADMmutate shell code"): 
        self.pname = pname
        self.fname = fname

    def generate(self, count, test=True):
        samples = []
        for i in xrange(count):
            sample = ""
            # sometimes admmutate fails and returns an empty string
            while not sample.endswith('confirm\n'):
                (fi,fo,fe) = os.popen3("admmutate")

                if test:
                    fi.write('echo "confirm"\n')
                    fi.write("exit\n")
			
                fi.close()
                sample = fo.read()
                if not test:
                    sample += 'confirm\n'
                if not sample.endswith('confirm\n'):
                    print "dud!"

            yield sample[:-8]

    ports = property(lambda self: [])
