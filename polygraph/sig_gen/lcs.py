#!/usr/bin/env python

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

        # switched to suffix tree implementation
        st = sutil.STree(pos_samples)
#        strings = st.common_sub(2, max(int(len(pos_samples)*3/4), 2)).keys()
        strings = st.common_sub(2, len(pos_samples), 2).keys()
        strings.sort(lambda x,y: cmp(len(y), len(x)))
        if len(strings) > 0:
            self.sig = strings[0]
        return [self]

        # CURRENTLY UNUSED
        # iterate from longest to shortest substrings.
        for sub_len in xrange(min(self.maxlen, len(pos_samples[0])), 1, -1):
            for start in xrange(len(pos_samples[0]) - sub_len + 1):
                sub = pos_samples[0][start:start+sub_len]

                # see if sub occurs in all other samples
                for sample in pos_samples[1:]:
                    if sample.find(sub) < 0:
                        break
                else:
                    # OK, use this one
                    self.sig = sub
                    print "LCS: " + self.sig_str()
                    return

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
