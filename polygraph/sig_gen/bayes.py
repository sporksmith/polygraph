#!/usr/bin/env python

from __future__ import division
import math
import sig_gen
import sys
import re
import polygraph.util.sutil as sutil
import sets
import polygraph.sigprob.sigprob as sigprob
import pickle

class Bayes(sig_gen.SigGen):
    fpos_rate = {}
    trace_fpos_rate = {}
    stats_fpos_rate = {}
    nostats_fpos_rate = {}

    def __init__(self, pname="Bayes", fname="bayes",
                minlen=2, maxlen=1000, kmin=2, kfrac=1.0, statsfile=None, prune=True, threshold_style='min', max_fpos=None, training_trace=None):
        self.minlen = minlen
        self.maxlen = maxlen
        self.pname = pname
        self.fname = fname
        self.token_scores = None
        self.tokens = None
        self.tokentree = None
        # set to 'min' or 'biggest_jump' or 'bound' or a number
        self.threshold_style = threshold_style
        self.max_fpos = max_fpos # used for 'bound' threshold
        self.threshold = None # score threshold for classification
        self.kmin = kmin
        self.kfrac = kfrac # threshold when finding tokens
        self.stats = None
        self.prune = prune
        self.training_trace = training_trace
        
        self.pos_samples = None

        if threshold_style == 'bound':
            assert(self.training_trace and self.max_fpos)

        if statsfile:
            try:
                f = open(statsfile)
                self.stats = pickle.load(f)
                f.close()
            except TypeError:
                self.stats = statsfile

    def set_threshold(self):
        """
        Set the threshold for the signature.
        """

        pos_samples = self.pos_samples
        if self.threshold_style == 'biggest_jump':
            # look for largest jump in scores in suspicious pool.
            # XXX: This doesn't work well, and shouldn't be used.
            sample_scores = [self.score(sample) for sample in pos_samples]
            sample_scores.sort()

            # look for biggest jump in score
            biggest = sample_scores[0]
            self.threshold = sample_scores[0]
            for i in xrange(1,len(sample_scores)):
                jump = sample_scores[i] - sample_scores[i-1]
                if jump > biggest:
                    biggest = jump
                    self.threshold = sample_scores[i]
        elif self.threshold_style == 'min':
            # use smallest threshold that will cause all samples in the
            # suspicious pool to match the signature.
            sample_scores = [self.score(sample) for sample in pos_samples]
            self.threshold = min(sample_scores)
        elif self.threshold_style == 'bound':
            # use threshold that results in sufficiently low false positives
            self.get_bound_threshold(pos_samples)
        else:
            # use a user-specified threshold.
            # This is an approximation of the 'bound' threshold style.
            # Given a 'target' false positive rate, a corresponding threshold
            # can be calculated.
            self.threshold = self.threshold_style

    def get_bound_threshold(self, pos_samples):
        top_neg_scores = []

        import polygraph.trace_crunching.stream_trace as stream_trace
        trace = stream_trace.StreamTrace(self.training_trace)
        sample = trace.next()
        while sample:
            score = self.score(sample)
            if len(top_neg_scores) < (self.max_fpos+1) or score > top_neg_scores[0]:
                top_neg_scores.append(score)
                top_neg_scores.sort()
                if len(top_neg_scores) > (self.max_fpos + 1):
                    del top_neg_scores[0]
            sample = trace.next()
        Tmin = top_neg_scores[0]
#        print 'Top negative scores: ', top_neg_scores
#        print 'Tmin: ', Tmin

        sample_scores = []
        for s in pos_samples:
            sample_scores.append(self.score(s))
        sample_scores.sort()
        # find lowest sample score that is > Tmin
        for score in sample_scores:
            if score > Tmin:
                Tmax = score
                break
        else:
            print "Can't satisfy threshold constraints!"
            self.threshold = Tmin
            return

#        print 'Tmax: ', Tmax
        fraction = (Tmax-Tmin)*.5
        self.threshold = Tmin+fraction

    def score(self, sample):
        sample_score = 0
        sample_tokens = self.get_sample_occurrences(sample, False, False) 

        sample_score = -math.log(.5)/math.log(10)

        for token in self.token_scores:
            if sample_tokens.has_key(token):
                sample_score += self.token_scores[token]

        return sample_score

    def train(self, pos_samples):
        if len(pos_samples) < 2:
            print pos_samples
            print len(pos_samples)
            print 'not enough samples. bug??'
            assert False

        # reinit
        self.token_scores = None
        self.tokens = None
        self.tokentree = None
        self.pos_samples = pos_samples

        stree = sutil.STree(pos_samples)
        tokens = stree.common_sub(self.minlen, min(len(pos_samples), max(self.kmin, int(self.kfrac*len(pos_samples)))), prune=self.prune)
        stree = None
        self.tokens = tokens.keys()
#        self.tokentree = sutil.STree(tokens.keys())

        token_strings = self.get_all_occurrences(pos_samples)
        self.token_scores = {}

        # calculate scores based on Bayes law
        for token in token_strings.keys():
            prob_tok_giv_worm = 1.0 * len(token_strings[token])  \
                                / len(pos_samples)
            prob_tok_giv_nworm = sig_gen.est_fpos_rate(token, 
                                                       self.training_trace)
            part = prob_tok_giv_nworm \
                   / (.5*prob_tok_giv_worm + .5*prob_tok_giv_nworm) + 1e-300
            token_score = max(-1 * math.log(part)/math.log(10),0)
            if token_score > 0:
                self.token_scores[token] = token_score

        # prevents a subtle bug later, when there turn out to be no
        # tokens kept. (i.e., they all had score 0)
        self.tokens = self.token_scores.keys()

        self.set_threshold()

        # Signature generation and signature matching code is tightly
        # coupled. TODO: refactor to return a separate signature object
        return [self]

    def match(self, sample):
        return self.score(sample) >= self.threshold

    def sig_str(self):
        sorted_tokens = self.token_scores.keys()
        sorted_tokens.sort(lambda x,y: cmp(self.token_scores[x], self.token_scores[y]))
        result = ['{']
        for t in sorted_tokens:
            result.append(t.__repr__())
            result.append(': ')
            result.append('%.4f, ' % self.token_scores[t])
        result.append('} Threshold: %.4f' % self.threshold)
        return ''.join(result)

    def __str__(self):
        return self.sig_str()

    def naive_get_token_dict(self, sample):
        """
        Get the tokens present in a sample, and their positions.
        
        This algorithm scans the sample string once for each token it is
        looking for. 
        """

        d = {}
        
        if self.token_scores:
            tokens = self.token_scores.keys()
        else:
            tokens = self.tokens

        for token in tokens:
            pos = 0
            while True:
                pos = sample.find(token, pos)
                if pos < 0:
                    break
                if not d.has_key(pos) or len(d[pos]) < len(token):
                    d[pos] = token
                pos += 1
        return d

    def get_token_list(self, sample, allow_containment=True, 
                       allow_overlap=True):
        """
        Get an ordered list of tokens occurring in a sample.

        Optionally allow or disallow tokens that are contained within
        other tokens or overlap with other tokens. When there is a conflict,
        use the most incriminating token (the one with the highest score).
        """

        # Get all the tokens that occur in the sample, and their positions.
        # XXX: suffix tree implementation should be faster, but doesn't seem
        # to be in practice. 
#        token_dict = self.tokentree.find_tokens(sample)
        token_dict = self.naive_get_token_dict(sample)

        positions = token_dict.keys()
        positions.sort()
        token_list = []

        # Go through tokens in the order that they appear, resolving any
        # overlap or containment conflicts.
        covered_to = 0
        for p in positions:
            # check for containment
            if not allow_containment and p + len(token_dict[p]) <= covered_to:
                if self.token_scores[token_dict[p]] > self.token_scores[token_list[-1]]:
                    del token_list[-1]
                else:
                    continue

            # check for overlap
            elif not allow_overlap and p < covered_to:
                if self.token_scores[token_dict[p]] > self.token_scores[token_list[-1]]:
                    del token_list[-1]
                else:
                    continue

            token_list.append(token_dict[p])
            covered_to = p + len(token_dict[p])

        return token_list

    def get_sample_occurrences(self, sample, allow_containment=True, 
                               allow_overlap=True):
        """
        Returns dictionaries of the number of occurences of each token.
        """

        seen_tokens = {}

        token_list = self.get_token_list(sample, allow_containment, allow_overlap)
        for token in token_list:
            if not seen_tokens.has_key(token):
                seen_tokens[token] = 1
            else:
                seen_tokens[token] += 1

        return seen_tokens

    def get_all_occurrences(self, samples):
        """
        Returns dictionaries mapping a token to the samples that contain it.
        """

        # map token -> (set of strings containing token)
        token_strings = {}

        for sample in samples:
            token_occ = self.get_sample_occurrences(sample)

            for token in token_occ:
                if not token_strings.has_key(token):
                    token_strings[token] = sets.Set()
                token_strings[token].add(sample)

        return token_strings


