#!/usr/bin/env python
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

import sig_gen
import sys
import re
#import polygraph.sigprob.sigprob as sigprob
import math
import cluster

#def tuple_match(tuple_sig, sample):
#    pos = 0
#    for token in tuple_sig:
#        new_pos = sample.find(token, pos)
#        if new_pos < 0:
#            return False
#        pos = new_pos + len(token)
#    return True

class TupleSig(sig_gen.Sig):
    def __init__(self, lcs, tuplesig):
        self.lcs = lcs
        self.tuplesig = tuplesig

    def match(self, sample):
        pos = 0
        for token in self.tuplesig:
            new_pos = sample.find(token, pos)
            if new_pos < 0:
                return False
            pos = new_pos + len(token)
        return True

    def __str__(self):
        return self.tuplesig.__repr__()

class RegexSig(sig_gen.Sig):
    def __init__(self, pattern):
        self.regex = re.compile(pattern, re.DOTALL)

    def match(self, sample):
        return self.regex.match(sample)

    def __str__(self):
        return self.regex.pattern.__repr__()

class LCSeqTree(sig_gen.SigGen):
    def __init__(self, pname="Longest Common Subsequence with Tree", fname="lcseq", gap_penalty=0.8, tokenize_pairs=True, tokenize_all=False, k=5, kfrac=0, minlen=2, use_fixed_gaps=False, do_cluster=True, spec_threshold=40, min_cluster_size=3, max_fp_count=None, fpos_training_streams=None, statsfile=None, bound_similarity=False, max_tokens_in_est=5):
        self.regex = None
        self.pname = pname
        self.fname = fname
        self.gap_penalty = gap_penalty
        self.lcs = ""
        assert not (tokenize_all and tokenize_pairs)
        self.tokenize_all = tokenize_all
        self.k = k
        self.kfrac = kfrac
        self.tokenize_pairs = tokenize_pairs
        self.minlen = minlen
        self.use_fixed_gaps = use_fixed_gaps
        self.do_cluster = do_cluster
        self.spec_threshold = spec_threshold
        self.min_cluster_size = min_cluster_size
        self.tuplesig = ()
        self.max_fp_count = max_fp_count
        self.fpos_training_streams = fpos_training_streams
        self.bound_similarity = bound_similarity
        self.max_tokens_in_est = max_tokens_in_est

        if use_fixed_gaps:
            raise NotImplementedError('use_fixed_gaps option is currently broken.')

#        if statsfile:
#            try:
#                f = open(statsfile)
#                import pickle
#                self.statsfile = pickle.load(f)
#                f.close()
#            except TypeError:
#                self.statsfile = statsfile
#        else:
#            self.statsfile = None


    def _find_lcs(self,a,b):
        import polygraph.util.pysubseq as pysubseq
        return pysubseq.lcseq(a,b,self.gap_penalty)

    def _lcs_to_tuple(self, lcs):
        l = []
        token = []
        for item in lcs:
            if item == 'GAP' or item == 'WILD':
                if len(token) > 0:
                    l.append("".join(token))
                    token = []
            else:
                token.append(item)
        if len(token) > 0:
            l.append("".join(token))

        return tuple(l)

    def _lcs_to_regex(self, lcs):
        regex_list = []
        count = 0
        for item in lcs:
            if item == 'GAP':
                regex_list.append('.*')
                count = 0
            elif item == 'WILD':
                count += 1
            else:
                if count > 0:
                    if self.use_fixed_gaps:
                        regex_list.append(".{%d}" % count)
                    else:
                        regex_list.append(".*")
                    count = 0
                regex_list.append("%s" % sig_gen.regex_esc(item))
        return ''.join(regex_list)

    def _tokenize_samples(self, samples):
        import polygraph.util.sutil as sutil
        st = sutil.STree(samples)
        tokens = st.common_sub(self.minlen, max(int(self.kfrac*len(samples)), min(self.k, len(samples)))).keys()
        st = None

        tokenized_samples = []
        for sample in samples:
            # start with wildcards or gaps everywhere
            if self.use_fixed_gaps:
                tokenized = ['WILD'] * len(sample)
            else:
                tokenized = ['GAP'] * len(sample)

            # fill in each occurrence of each token
            # XXX: more efficient with suffix tree
            for token in tokens:
                start = 0
                while True:
                    pos = sample.find(token, start)
                    if pos < 0: break
                    for c_i in xrange(len(token)):
                        tokenized[pos+c_i] = token[c_i]
                    start = pos + 1

            if not self.use_fixed_gaps:
                # delete multiple gaps
                for i in xrange(len(tokenized)-1, 0, -1):
                    if tokenized[i] == 'GAP' and tokenized[i-1] == 'GAP':
                        del tokenized[i]

            tokenized_samples.append(tokenized)

        return tokenized_samples

    def train(self, pos_samples):
        if self.tokenize_all:
            pos_samples = self._tokenize_samples(pos_samples)

        if self.do_cluster:
            def sig_gen_cb(left, right):
                lsig = left['sig']
                rsig = right['sig']

                # tokenize if possible
                if not lsig and not rsig and self.tokenize_pairs:
                    lsig = pos_samples[left['samples'][0]]
                    rsig = pos_samples[right['samples'][0]]
                    (lsig, rsig) = self._tokenize_samples([lsig, rsig])
                else:
                    if lsig:
                        lsig = lsig.lcs
                    else:
                        lsig = list(pos_samples[left['samples'][0]])
                    if rsig:
                        rsig = rsig.lcs
                    else:
                        rsig = list(pos_samples[right['samples'][0]])

                # find the common subsequence
                lcs = self._find_lcs(lsig, rsig)
                t = self._lcs_to_tuple(lcs)
                sig = TupleSig(lcs, t)
#                print self._lcs_to_regex(sig)

                # calculate a score for the resulting signature
                scores = []
                for token in t:
#                    prob = sigprob.regex_prob(token, 1000, stats=self.statsfile)[-1]
                    prob = sig_gen.est_fpos_rate(token, self.fpos_training_streams)
                    scores.append(- math.log(prob + 1e-300)/math.log(10))

                # using all the token scores overly favors signatures
                # with many tokens. Current fix is to only use most distinctive
                # tokens to calculate the score.
                if self.max_tokens_in_est:
                    scores.sort(lambda x,y: cmp(y,x))
                    score = sum(scores[:self.max_tokens_in_est])
                else:
                    score = sum(scores)
                return (sig, score)

            import cluster
            clusters = cluster.cluster(sig_gen_cb, self.spec_threshold, 
                              pos_samples, max_fp_count = self.max_fp_count,
                              fpos_training_streams=self.fpos_training_streams,
                              min_cluster_size=self.min_cluster_size,
                              bound_similarity=self.bound_similarity)

            # return the tuple signatures for the final clusters
            self.tuple_list = []
            sigs = []
            for c in clusters:
                if len(c['samples']) >= self.min_cluster_size:
                    self.tuple_list.append(c['sig'].tuplesig)
                    sigs.append(c['sig'])
            self.clusters = clusters
            return sigs

        else:
            # Find a subsequence common to all the samples
            self.lcs = pos_samples[0]
            for sample in pos_samples[1:]:
                self.lcs = self._find_lcs(self.lcs, sample)

            # Return the final signature
            regex_string = self._lcs_to_regex(self.lcs)
            if self.use_fixed_gaps:
                return [RegexSig(self._lcs_to_regex(self.lcs))]
            else:
                return [TupleSig(self.lcs, self._lcs_to_tuple(self.lcs))]

#    def match(self, sample):
#        if self.use_fixed_gaps:
#            return bool(self.regex.match(sample))
#        else:
#            for t in self.tuple_list:
#                if tuple_match(t, sample):
#                    return True
#            return False
#
#    def __str__(self):
#        if self.use_fixed_gaps:
#            return self.regex.pattern
#        else:
#            return self.tuple_list.__repr__()

#def test():
#    samples = []
#    samples.append("gagghua one afehauifheau two heuighriga three")
#    samples.append("afeaffeafea one grhugeegvbn two agrgexz three")
#    samples.append("one ghuah two paenv three feahuone")
#
##    sig = LCSeq()
#    print "Exact:"
#    sig.train(samples)
#    print sig.regex.pattern
#
##    sig = LCSeqApprox()
#    print "Approximate:"
#    sig.train(samples)
#    print sig.regex.pattern
#
#if __name__ == "__main__":
#    samples = []
#
#    # if there's multiple files, consider each file as a sample
#    if len(sys.argv) > 2:
#        for fname in sys.argv[1:]:
#            f = open(fname)
#            samples.append(f.read())
#            f.close()
#    # if there's just one, consider each line as a sample
#    elif len(sys.argv) == 2:
#        f = open(sys.argv[1])
#        samples = f.readlines()
#    # otherwise, nothing to do
#    else:
#        print "Need to specify file(s)!"
#        sys.exit()
#
#    sig = LCSeqTree()
#    sig.train(samples)
#    print sig.sig_str()
##    tokens = _get_tokens(samples,4,10)
##    print _tuples_to_regex(_find_sig_with_tokens(samples, tokens))
