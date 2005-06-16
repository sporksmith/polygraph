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
