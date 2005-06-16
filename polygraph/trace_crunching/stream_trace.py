#!/usr/bin/env python

from __future__ import division
import sys
import struct

def best_substrings(samples, streamfile):
    # find tokens that occur in _EVERY_ sample
    import sutil
    st = sutil.STree(samples)
    tokens = st.common_sub(2, len(samples)).keys()

    (total, counts) = token_counts(tokens, streamfile)

    # output sorted list of tokens & fp counts
    tokens.sort(lambda x,y: cmp(counts[y], counts[x]))
    for t in tokens:
        print t.__repr__(), counts[t], counts[t] / total

# return (total samples in file, {token: count, token: count, ...})
def token_counts(tokens, streamfile):
    total = 0
    counts = {}
    for t in tokens:
        counts[t] = 0

    trace = StreamTrace(streamfile)
    stream = trace.next()
    while stream:
        total += 1
        for t in tokens:
            if stream.find(t) >= 0:
                counts[t] += 1
        stream = trace.next()
    return (total, counts)

def regex_count(pattern, streamfile):
    import re
    sig = re.compile(pattern, re.DOTALL)

    total = 0
    count = 0

    trace = StreamTrace(streamfile)
    stream = trace.next()
    while stream:
        total += 1
        if sig.match(stream):
            count += 1
        stream = trace.next()
    return (count, total)

class StreamTrace(object):
#    def __init__(self, filename):
#        self.tracefile = open(filename)
#        self.longlen = struct.calcsize('I')
#    def next(self):
#        packed_length = self.tracefile.read(self.longlen)
#        if len(packed_length) != self.longlen:
#            self.tracefile.close()
#            return None
#        (length,) = struct.unpack('I', packed_length)
#        stream = self.tracefile.read(length)
#        assert(len(stream) == length)
#        return stream
    def __init__(self, filename):
        self.filename = filename
        self.tracefile = open(filename + '/data')
        self.offsetsfile = open(filename + '/offsets')

        longlen = struct.calcsize('L')
        (self.last_off,) = struct.unpack('L', self.offsetsfile.read(longlen))
        if self.last_off != 0:
            print self.last_off
            raise 'Invalid offsets file'

    def next(self):
        longlen = struct.calcsize('L')
        packed = self.offsetsfile.read(longlen)
        if len(packed) == 0: # end of file
            # last stream is rest of the file
            data = self.tracefile.read()

            # if we've already gotten the last stream, return None
            if len(data) == 0:
                data = None
            return data

        (next_off,) = struct.unpack('L', packed)
        length = next_off - self.last_off
        self.last_off = next_off
        return self.tracefile.read(length)

    def numstreams(self):
        import os
        s = os.fstat(self.offsetsfile.fileno())
        return s.st_size // struct.calcsize('L')

    def seek(self, streamno):
        assert(streamno < self.numstreams())
        self.offsetsfile.seek(streamno * struct.calcsize('L'))
        (self.last_off,) = struct.unpack('L', self.offsetsfile.read(struct.calcsize('L')))
        self.tracefile.seek(self.last_off)

if __name__ == "__main__":
#    import pkts_to_streams
#    outfile = open(sys.argv[1], 'w')
#
#    def callback(stream):
#        if len(stream['data']) > 0:
#            outfile.write(struct.pack('L', len(stream['data'])))
#            outfile.write(stream['data'])
#
#    for trace in sys.argv[2:]:
#        pkts_to_streams.process_trace(trace, 
#                                        callback=callback, 
#                                        timeout=60,
#                                        filter=None)
#
#    outfile.close()

    import polygraph.trace_crunching.pkts_to_streams as pkts_to_streams
    import os
    import struct

    dirname = sys.argv[1]
    os.mkdir(dirname)
    dataname = dirname + '/data'
    datafile = open(dataname, 'w')
    offname = dirname + '/offsets'
    off_file = open(offname, 'w')

    offset = 0
    def callback(stream):
        if len(stream['data']) > 0:
            global offset
            off_file.write(struct.pack('L', offset))
            datafile.write(stream['data'])
            offset += len(stream['data'])

    for trace in sys.argv[2:]:
        pkts_to_streams.process_trace(trace, 
                                        callback=callback, 
                                        timeout=60,
                                        filter=None)

    off_file.close()
    datafile.close()
