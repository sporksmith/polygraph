#!/usr/bin/env python

from __future__ import division
import sys
import os
import struct
import polygraph.util.pysary as pysary

class TraceSary(object):
    def __init__(self, streamfile):
        # for offsets file
        self.f = None
        self.mx = None
        self.offsets_length = None

#        self.sary_file = streamfile + '.sarray/data'
#        self.offsets_file = streamfile + '.sarray/offsets'
        self.sary_file = streamfile + '/data'
        self.offsets_file = streamfile + '/offsets'

        self.sary = pysary.saryer_new(self.sary_file)
        if self.sary == 'NULL':
            import exceptions
            self.sary = None
            raise exceptions.Exception("Couldn't open sarray %s for %s" % \
                  (self.sary_file, streamfile))

        self.numstreams = int(os.path.getsize(self.offsets_file) / 4)
        self.length = os.path.getsize(self.sary_file)


    def __del__(self):
        if self.sary:
            pysary.saryer_destroy(self.sary)
            self.sary = None
        if self.mx:
#            self.mx.close()
#            os.close(self.f)
            self.f.close()

    def offset_to_index(self, offset, start=0):
        import mmap, os, struct
#        fname = streamfile + '.sarray/offsets'

        if not self.mx:
            self.offsets_length = os.path.getsize(self.offsets_file)
            self.f = open(self.offsets_file)
#            self.f = os.open(self.offsets_file, os.O_RDWR)
#            self.mx = mmap.mmap(self.f, self.offsets_length)
            self.mx = self.f.read()

        def value(x):
            return struct.unpack('l', self.mx[x*4:(x+1)*4])[0]

        startvalue = value(start)
        end = int(self.offsets_length / 4) 
#       endvalue = value(end)
        while True:
            current = int((end + start)/ 2) 
#           (thisone,) = struct.unpack('l', mx[(current*4):(current+1)*4])
            thisone = value(current)
#           print start,end, current, thisone

            if current == int(self.offsets_length / 4 - 1):
                # eof
                nextone = None 
                break

            nextone = value(current+1)
            if thisone <= offset < nextone:
                break
            elif end == (start + 1):
                end += 1
            elif offset < thisone:
                end = current
            elif offset >= nextone:
                start = current
            else:
                assert(False)

        return (current, nextone)

    def token_count(self, token):
#        if not pysary.saryer_search2(self.sary, token, len(token)):
        if not pysary.saryer_search2(self.sary, token):
            return 0
        return pysary.saryer_count_occurrences(self.sary)

    def token_count_unique(self, token, estimate=False):
#        if not pysary.saryer_search2(self.sary, token, len(token)):
        if not pysary.saryer_search2(self.sary, token):
            return 0
        pysary.saryer_sort_occurrences(self.sary)
        count = pysary.saryer_count_occurrences(self.sary)

        nextone = 0
        uniquecount = 0
        streami = 0
        for i in xrange(count):
            fileoffset = pysary.saryer_get_next_offset(self.sary)
            assert(fileoffset >= 0)
            if fileoffset < nextone:
                continue
            uniquecount += 1
            if estimate:
                nextone = fileoffset + int(self.length/self.numstreams) # hack
            else:
                (streami, nextone) = self.offset_to_index(fileoffset)#, start=streami)
#               print streami, fileoffset, nextone
#            sys.stdin.readline()

            if not nextone:
                break

        return uniquecount

#
#if __name__ == "__main__":
#    import polygraph.trace_crunching.stream_trace as stream_trace
#    import os
#    import struct
##    dirname = sys.argv[1] + '.sarray'
#    dirname = sys.argv[1] + '.sarray'
#    os.mkdir(dirname)
#    dataname = dirname + '/data'
#    datafile = open(dataname, 'w')
#    offname = dirname + '/offsets'
#    off_file = open(offname, 'w')
#    offset = 0
#    
#    trace = stream_trace.StreamTrace(sys.argv[1])
#    stream = trace.next()
#    while stream:
#        datafile.write(stream)
#        off_file.write(struct.pack('l', offset))
#        offset += len(stream)
#        stream = trace.next()
#
