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
import sutil

class LCS(sig_gen.SigGen):
    def __init__(self, maxlen=1000, fname="lcs", pname="Longest Common Substring"):
        self.sig = ""
        self.maxlen= maxlen
        self.fname = fname
        self.pname = pname

    def sig_str(self):
#        return sig_gen.regex_esc(self.sig)
        return self.sig.__repr__()

    def __str__(self):
        return self.sig_str()

    def train(self, pos_samples):
        self.sig = ""

        # find longest common substring
        st = sutil.STree(pos_samples)
        strings = st.common_sub(2, len(pos_samples), prune=False).keys()
        strings.sort(lambda x,y: cmp(len(y), len(x)))
        if len(strings) > 0:
            self.sig = strings[0]
        return [self]

    def match(self, sample):
        return sample.find(self.sig) >= 0

def test():
    samples = []
    samples.append("gagghua one afehauifheau two heuighriga three")
    samples.append("afeaffeafea one grhugeegvbn two agrgexz three")
    samples.append("one ghuah two paenv three feahuone")

    sig = LCS()
    sig.train(samples)

    print sig.regex.pattern

if __name__ == "__main__":
    samples = []

    # if there's multiple files, consider each file as a sample
    if len(sys.argv) > 2:
        for fname in sys.argv[1:]:
            f = open(fname)
            samples.append(f.read())
            f.close()
    # if there's just one, consider each line as a sample
    elif len(sys.argv) == 2:
        f = open(sys.argv[1])
        samples = f.readlines()
    # otherwise, nothing to do
    else:
        print "Need to specify file(s)!"
        sys.exit()

    sig = LCS()
    sig.train(samples)
    print sig.sig_str()
#    tokens = _get_tokens(samples,4,10)
#    print _tuples_to_regex(_find_sig_with_tokens(samples, tokens))
