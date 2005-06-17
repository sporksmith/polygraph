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
from __future__ import division

def tokenprob(token, streamfile):
    import os
    import re
    import polygraph.trace_crunching.sarray_trace as sarray_trace

    ts = sarray_trace.TraceSary(streamfile)
    return min(1, ts.token_count(token) / ts.numstreams)

#    return sarray_trace.token_count(streamfile, token) / 59741
#    sary = pysary.saryer_new(streamfile)
    count = 0
    if pysary.saryer_search2(sary, token, len(token)):
        count = pysary.saryer_count_occurrences(sary)
    pysary.saryer_destroy(sary)

    return min(1, count/59741)

def split(token, stats, maxcontextlen=2):
    start = 0
    for end in xrange(1,len(token)):
        contextlen = min(end-start, maxcontextlen)
        context = token[end-contextlen:end]
        byte = token[end]
#        print contextlen, context.__repr__(), byte.__repr__(),

        if not stats['']['bytes'].has_key(byte):
#            print byte.__repr__(), 0
            continue

        if stats.has_key(context) and stats[context]['bytes'].has_key(byte):
            nocontextprob = stats['']['bytes'][byte]/stats['']['count']
            contextprob = stats[context]['bytes'][byte]/stats[context]['count']
            print byte.__repr__(), nocontextprob, contextprob, contextprob/nocontextprob
#            print byte.__repr__(), int(10*stats[context]['bytes'][byte]/stats[context]['count']) % 10
            if (stats['']['bytes'][byte]/stats['']['count']) > (stats[context]['bytes'][byte]/stats[context]['count']):
#                print token[start:end] 
                start = end

def mpp_old(token,tracefile=None,minprob=1,minlen=1):
    import sigprob

    # return probability of a particular token
    def token_prob(t):
        return tokenprob(t, tracefile)
#        return (stcounts[t] / tracetotal)
#        return sigprob.regex_prob(t, 1000, stats=stats)[-1]

    # recursive helper, takes start and end of token
    mpp_cache = {} # memoize
    def mpp_helper(start, end):
#        print token[start:end]
        if mpp_cache.has_key((start,end)):
            return mpp_cache[(start,end)]
        assert(start != end)
        if end == len(token):
            return (token_prob(token[start:]), [token[start:]])
        splitprob = token_prob(token[start:end])*mpp_helper(end,end+1)[0]
        nosplitprob = mpp_helper(start, end+1)[0]
        if splitprob > nosplitprob and nosplitprob < minprob and (end-start) > minlen:
            rv = (splitprob, [token[start:end]] + mpp_helper(end,end+1)[1])
        else:
            rv = (nosplitprob, mpp_helper(start, end+1)[1])
        mpp_cache[(start,end)] = rv
        return rv

    return mpp_helper(0, 1)

# bottom up implementation of mpp
def mpp(token,tracefile=None,minprob=1,minlen=1):
    lastline = []
    thisline = []

    import polygraph.trace_crunching.sarray_trace as sarray_trace
    ts = sarray_trace.TraceSary(tracefile)
    def tokenprob(t):
        return min(.999, ts.token_count(t) / ts.numstreams)
#        return min(1, ts.token_count_unique(t) / ts.numstreams)
#        return min(1, ts.token_count_unique(t, estimate=True) / ts.numstreams)

    end = len(token)
    for start in xrange(len(token)):
        lastline.append((tokenprob(token[start:]), [(start, end)]))

    for end in xrange(len(token)-1, 0, -1):
        for start in xrange(end):
            splitprob = tokenprob(token[start:end]) * lastline[end][0]
            nosplitprob = lastline[start][0]
            if splitprob > nosplitprob and nosplitprob < minprob and (end-start) > minlen:
                thisline.append((splitprob, [(start, end)] + lastline[end][1]))
            else:
                thisline.append((nosplitprob, lastline[start][1]))
#        print thisline
        lastline = thisline
        thisline = []

    split = []
    for (start, end) in lastline[0][1]:
        split.append(token[start:end])
    return lastline[0][0], split

def token_counts_mult(tokens, streamfile):
    import os
    import re
    import polygraph.util.pysary as pysary
    import polygraph.trace_crunching.sarray_trace as sarray_trace

    counts = {}
    tsary = sarray_trace.TraceSary(streamfile)
    for t in tokens:
        counts[t] = tsary.token_count(t)
    return (tsary.length, tsary.numstreams, counts)

#    counts = {}
#    sary = pysary.saryer_new(streamfile)
#
#    for t in tokens:
#        count = 0
#        if pysary.saryer_search2(sary, t):
#            count = pysary.saryer_count_occurrences(sary)
#        counts[t] = count
#    pysary.saryer_destroy(sary)
#
#    return (59741000, counts)

#    import stream_trace
#    total = 0
#    counts = {}
#    for t in tokens:
#        counts[t] = 0
#
#    trace = stream_trace.StreamTrace(streamfile)
#    stream = trace.next()
#    while stream:
#        total += len(stream)
#        for t in counts.keys():
#            counts[t] += stream.count(t)
#        stream = trace.next()
#    return (total, counts)

def maxcontextprob(token, tracefile=None, stats=None, maxlen=10):
    import sigprob

    if not maxlen:
        maxlen = len(token)

    if not stats:
        assert(tracefile)

        # find probabilities of all subtokens
#        print "Generating subtokens"
        import sets
        subtokens = sets.Set()
        for start in xrange(len(token)):
            for end in xrange(start+1, min(len(token), start+maxlen)+1):
                subtokens.add(token[start:end])
#        print "Crunching trace"
        (bytetotal, numstreams, stcounts) = token_counts_mult(subtokens, tracefile)
        subtokens = None

        # build statistics
#        print "Building stats"
        stats = {}
        stats[''] = {'count': bytetotal, 'bytes': {}}
        for st in stcounts.keys():
            stats[st] = {'count': stcounts[st], 'bytes': {}}
        for byte in xrange(len(token)):
            for contextstart in xrange(max(0, byte-maxlen+1), byte+1):
                context = token[contextstart:byte]
                stats[context]['bytes'][token[byte]] = stcounts[token[contextstart:byte+1]]

    # calculate probability
#    print Calculating probability"
    return sigprob.regex_prob(token, int(bytetotal/numstreams), stats=stats, max_context=maxlen)[-1], stats
