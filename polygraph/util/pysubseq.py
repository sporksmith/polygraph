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
import pysubseqc 

def lcseq(seq1, seq2, gap_penalty=.8):
    numseq1 = []
    for i in xrange(len(seq1)):
        if seq1[i] == 'GAP':
            numseq1.append(256)
        else:
            numseq1.append(ord(seq1[i]))

    numseq2 = []
    for i in xrange(len(seq2)):
        if seq2[i] == 'GAP':
            numseq2.append(256)
        else:
            numseq2.append(ord(seq2[i]))

    numsubseq = pysubseqc.lcseq(numseq1, numseq2, gap_penalty)
    subseq = []
    for i in xrange(len(numsubseq)):
        if numsubseq[i] == 256:
            subseq.append('GAP')
        else:
            subseq.append(chr(numsubseq[i]))

    return subseq
