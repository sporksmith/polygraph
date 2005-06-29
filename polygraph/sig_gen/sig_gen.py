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
import string

class SigGen(object):
    """
    Abstract class for signature generation factories.
    """

    def __init__(self, pname="Pretty Name", fname="filename"): pass

    def train(self, pos_samples):
        """
        Generate one or more signatures from pos_samples (suspicious pool).
        Returns a sequence of Sig objects.
        """
        raise NotImplementedError

class Sig(object):
    """
    Abstract signature class.
    """

    def match(self, sample):
        "Return whether current signature matches the sample"
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


def regex_esc(s):
    escaped = []
    for c in s:
        if c.isalnum():
            escaped.append(c)
        elif c == ' ':
            escaped.append("\\ ")
        elif c == "\t":
            escaped.append("\\t")
        elif c == "\n":
            escaped.append("\\n")
        elif c == "\r":
            escaped.append("\\r")
        elif string.punctuation.find(c) >= 0:
            escaped.append("\\%s" % c)
        else:
            escaped.append("\\x%02x" % ord(c))
    return ''.join(escaped)

estd_fpos_rate = {} # memoize
def est_fpos_rate(token, trace=None, stats=None):
    """
    Estimate false positive rate of a single-token signature.
    
    Estimates using the 'tokensplit' and trace-modeling methods,
    and returns the higher (most pessimistic of the two). Note that both
    of these estimates are strictly equal to or higher than the actual 
    fraction of streams that 'token' occurs in within the trace.
    """

    global estd_fpos_rate

    # if we don't have it cached, figure it out
    if not (estd_fpos_rate.has_key(trace) and estd_fpos_rate[trace].has_key(token)):
        # make sure there's a dictionary for this trace
        if not estd_fpos_rate.has_key(trace):
            estd_fpos_rate[trace] = {}

        # use most pessimistic (highest) estimate 
        import polygraph.sigprob.tokensplit as tokensplit
        import polygraph.sigprob.sigprob as sigprob
        if trace:
            split_prob = tokensplit.mpp(token, trace, minlen=3)[0]
            stat_prob = tokensplit.maxcontextprob(token, trace)[0]
            estd_fpos_rate[trace][token] = max(split_prob, stat_prob)
        else:
            estd_fpos_rate[trace][token] = sigprob.token_prob(token, 1000, stats=stats)[-1]
    rv = estd_fpos_rate[trace][token]

    # conserve memory
    if len(token) > 20:
        del estd_fpos_rate[trace][token]
    if len(estd_fpos_rate[trace].keys()) > 200:
        estd_fpos_rate[trace].clear() # XXX should delete least recently accessed

    return rv
