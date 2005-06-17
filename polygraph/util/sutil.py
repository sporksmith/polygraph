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
import sutilc

#created = 0
#deleted = 0

class STree(object):
#    handle = None
    def __init__(self, strings):
        # copy the list of strings, but not the strings themselves.
        # c implementation keeps pointers into the strings, so
        # important to keep refs here to prevent strings from being
        # garbage collected.
        self.strings = strings[:]
        self.handle = sutilc.st_create(strings)
#        global created
#        global deleted
#        created += 1
#        print "created %d\tdeleted %d" % (created, deleted)

    def __del__(self):
        if self.handle:
            sutilc.st_destroy(self.handle)
            self.handle = None
#        global created
#        global deleted
#        deleted += 1
#        print "created %d\tdeleted %d" % (created, deleted)

    def find(self, s):
        return sutilc.st_find(self.handle, s)

    def find_tokens(self, s):
        tokens = sutilc.py_find_tokens(self.handle, s)
        for t in tokens.keys():
            tokens[t] = self.strings[tokens[t]]
        return tokens

    def add(self, s):
        sutilc.st_add(self.handle, s)
        self.strings.append(s)

    def common_sub(self, min_len, min_occ, prune=True):
        token_counts = sutilc.common_substrings(self.handle, min_len, min_occ)

        if not prune:
            return token_counts
        
        # undo double counts due to tokens appearing inside other tokens

        sorted_tokens = token_counts.keys()
        sorted_tokens.sort(lambda x,y: cmp(len(y), len(x)))


        for token_sub_i in xrange(len(sorted_tokens)):
            token_sub = sorted_tokens[token_sub_i]
            for token_super_i in xrange(token_sub_i):
                token_super = sorted_tokens[token_super_i]
                count = token_super.count(token_sub)
                if not count: continue
                for (string, super_count) in token_counts[token_super].items():
                    token_counts[token_sub][string] -= super_count * count

        
#        token_tree = STree(sorted_tokens)
#        # go through tokens from longest to shortest
#        for token in sorted_tokens:
#            # see where this token appears in larger (super) tokens
#            token_occurrences = token_tree.find(token)
#
#            # for each super token, and 
#            # how many times it occurred inside that token...
#            for (super_token_ind, count) in token_occurrences.items():
#                super_token = token_tree.strings[super_token_ind]
#                if super_token == token: continue
##                print "%s occurs inside %s %d times" % (token.__repr__(), super_token.__repr__(), count)
#                # subtract out the double counts in the token_counts where
#                # the current token appeared inside the super token
#                for (string, super_count) in token_counts[super_token].items():
##                    print "supertoken appears in string %d %d times" % (string, token_counts[super_token][string])
#                    token_counts[token][string] -= token_counts[super_token][string] * count
#        token_tree = None
                        
        # now prune out the tokens that no longer appear in enough
        # distinct strings
        for token in token_counts.keys():
            unique_count = 0
            for (string, count) in token_counts[token].items():
                if count > 0:
                    unique_count += 1
                else:
                    del(token_counts[token][string])
            if unique_count < min_occ:
                del(token_counts[token])

        return token_counts
