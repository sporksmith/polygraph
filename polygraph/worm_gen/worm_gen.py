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
