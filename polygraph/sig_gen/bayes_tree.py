#!/usr/bin/env python

import sig_gen
import sys
import math
import cluster
import bayes

class BayesTree(sig_gen.SigGen):
    def __init__(self, pname="Bayes with Tree", fname="bayes_tree", minlen=2, spec_threshold=40, min_cluster_size=3, kmin=2, kfrac=1.0, statsfile=None, threshold_style=None, max_fp_count=None, fpos_training_streams=None, bound_similarity=False, max_tokens_in_est=5):
        self.pname = pname
        self.fname = fname
        self.minlen = minlen
        self.spec_threshold = spec_threshold
        self.min_cluster_size = min_cluster_size
        self.clusters = []
        self.statsfile = statsfile
        self.kmin = kmin
        self.kfrac = kfrac
        self.threshold_style = threshold_style
        self.max_fp_count = max_fp_count
        self.fpos_training_streams = fpos_training_streams
        self.bound_similarity = bound_similarity
        self.max_tokens_in_est = max_tokens_in_est

        if statsfile:
            try:
                f = open(statsfile)
                import pickle
                self.statsfile = pickle.load(f)
                f.close()
            except TypeError:
                self.statsfile = statsfile


    def train(self, pos_samples):
            def sig_gen_cb(left, right):
                samples = [pos_samples[s] for s in left['samples'] + 
                          right['samples']]
                new_sig = bayes.Bayes(minlen=self.minlen, 
                                      kmin=self.kmin, kfrac=self.kfrac, 
                                      prune=True, 
                                      statsfile=self.statsfile,
                                      threshold_style='min',
                                      max_fpos=self.max_fp_count,
                                      training_trace=self.fpos_training_streams)
                                  
                new_sig.train(samples)
#                score = min([new_sig.score(s) for s in samples])
                score = new_sig.threshold
                token_scores = new_sig.token_scores.values()
                if self.max_tokens_in_est:
                    token_scores.sort(lambda x,y: cmp(y,x))
                    score = sum(token_scores[:self.max_tokens_in_est])
                else:
                    score = sum(token_scores)
                return (new_sig, score)

            import cluster
            self.clusters = cluster.cluster(sig_gen_cb, self.spec_threshold, 
                                   pos_samples, 
                                   max_fp_count=self.max_fp_count,
                                   fpos_training_streams=self.fpos_training_streams,
                                   bound_similarity=self.bound_similarity)

            if self.threshold_style != 'min':
                for c in self.clusters:
                    if c['sig']:
                        c['sig'].set_threshold()

            sigs = []
            for c in self.clusters:
                if len(c['samples']) >= self.min_cluster_size:
                    sigs.append(c['sig'])
            return sigs

    def match(self, sample):
        for c in self.clusters:
            if len(c['samples']) >= self.min_cluster_size and c['sig'].match(sample):
                return True
        return False

    def sig_str(self):
        sig_strings = []
        for c in self.clusters:
            if len(c['samples']) >= self.min_cluster_size:
                sig_strings.append(str(c['sig']))
        return ''.join(sig_strings)

    def __str__(self):
        return self.sig_str()
