import worm_gen
from worm_gen import random_bytes
import string
import os

class Clet(worm_gen.WormGen):
    """
    Generates polymorphic shellcode using the Clet polymorphic engine.
    """

    def __init__(self, fname="clet", 
                pname="clet shell code"): 
        self.pname = pname
        self.fname = fname

    def generate(self, count, test=True):
        samples = []
        while len(samples) < count:
            if test:
                (fi,fo,fe) = os.popen3("clet -d -e")

                # test that shellcode works
                fi.write('echo "confirm"\n')
                fi.write("exit\n")
                fi.close()
            else:
                (fi,fo,fe) = os.popen3("clet -d")

            s = fo.read()

            if test:
                if s.endswith('confirm\n'):
                    samples.append(s[:-8])
            else:
                samples.append(s)
        return samples


    ports = property(lambda self: [])
