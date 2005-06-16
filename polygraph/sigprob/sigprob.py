#!/usr/bin/env python

from __future__ import division
import re
#import priorprob

def contextprob(context, byte, stats, max_context=2, a_size=256):
    if stats == None:
        return 1/a_size

    context = context[max(len(context)-max_context,0):]

#    # if there's no data on this context, try one shorter
#    # currently assuming that there's a context for the empty string, which
#    # there should be if any data is contained at all
#    while (not stats.has_key(context) or 
#           not stats[context]['bytes'].has_key(byte))
#           and len(context) > 0:
#            context = context[1:]
#
#    # if there is
#    if stats[context]['bytes'].has_key(byte):
#        count = stats[context]['bytes'][byte]
#    else:
#        count = 1

    prob = 1/stats['']['count']
    lastcontext = ''
    while True:
        if stats.has_key(context) and stats[context]['count'] > 0 and stats[context]['bytes'].has_key(byte):
#            prob = max(prob, stats[context]['bytes'][byte]/stats[context]['count'])
            thisprob = stats[context]['bytes'][byte]/stats[context]['count']
            if thisprob > prob:
                prob = thisprob
                lastcontext = context
        if len(context) == 0:
            break

        context = context[1:]
#    print prob, lastcontext.__repr__(), byte.__repr__()

    return prob
#    return count / stats[context]['count']


def print_transitions(in_transitions):
    out_transitions = [[] for i in in_transitions]

    for to_state in xrange(len(in_transitions)):
        for (from_state, prob) in in_transitions[to_state]:
            out_transitions[from_state].append((to_state, prob))

    for state in xrange(len(out_transitions)):
        print "State %d:" % state
        total = 0
        for (to_state, prob) in out_transitions[state]:
            total += prob
            print "\t(%d,%f)" % (to_state, prob)
        print "\tProb sum: %f" % total

#class Edge:
#    def __init__(self, fromstate, tostate, prob):
#        self.fromstate = fromstate
#        self.tostate = tostate
#        self.prob = prob
#
#class State:
#    def __init__(self):
#        self.in_edges = []
#        self.prob = 0
#
#    def add_in_edge(self, edge):
#        self.in_edges.append(edge)
#
#class FSM:
#    def __init__(self):
#        # first state is start state, last is accept
#        states = [State()]
#
#    def add_edge(self, fromstate, tostate, prob):
#        pass

# add states to match the substring token at the end of the current fsm.
# failed matches go to last state that was already in the fsm, which is assumed
# to be a .*
def add_substring(token, transitions, a_size, stats, max_context=2):
    t_len = len(token)
    init_state = len(transitions) - 1

    # match transitions
    for i in xrange(t_len):
        transitions.append([(init_state+i, 
            contextprob(token[:i], token[i], stats, a_size=a_size, max_context=max_context))])

    # mismatch transitions
    # track how many previous characters match prefix of the token
    prefix_len = 0
    for i in xrange(t_len):
        # running count of current overlap with prefix
        if token[i] == token[prefix_len]:
            prefix_len += 1
        else:
            prefix_len = 0

        # if the prefix is the whole string we've processed so far, a
        # a mismatch goes back to the beginning 
        if prefix_len == i+1:
            return_point = 0
        else:
            return_point = prefix_len

        # add the mismatch transitions
        # keep in mind that mismatched character may be able to match
        # the character after the return point
        thischarprob = contextprob(token[:i], token[i], stats, a_size=a_size, max_context=max_context)
        after_return_prob = contextprob(token[:return_point], token[return_point], stats, a_size=a_size, max_context=max_context)
        if token[return_point] == token[i]: 
            transitions[init_state+return_point].append((init_state+i, 
                                                        1-thischarprob))
#                                                        (a_size-1)/a_size))
        else:
            # special case in binary, 
            # since there can only be 1 mismatch case
            if a_size == 2:
                transitions[init_state+return_point+1].append((init_state+i, 
                                                        1-thischarprob))
#                                                        (a_size-1)/a_size))
            else:
                transitions[init_state+return_point].append((init_state+i, 
                                        (1-thischarprob) * (1-after_return_prob)))
#                                                        (a_size-1)/a_size * \
#                                                        (a_size-1)/a_size))
                transitions[init_state+return_point+1].append((init_state+i, 
                                        (1-thischarprob) * after_return_prob))
#                                                        (a_size-1)/a_size * \
#                                                        1/a_size))
    # add in mismatch transition from state 0 to itself
#    transitions[init_state].append((init_state, (a_size-1)/a_size))



# computes and returns probabilities of being in each state after n steps
# assumes you start in state 0
# transitions[x] = [(y, p1),(z, p2)] indicates that y and z have transitions
# into x, with probabilities p1 and p2 that those are taken, respectively
def fsm_prob(transitions, n):
    num_states = len(transitions)
    final_after = [0] # probability reached final state after i transitions

    # initial probability of being in state 0 is 1, all other states 0
    oldstate_prob = [0 for i in xrange(num_states)]
    oldstate_prob[0] = 1

    # iteratively compute probabilities after taking n steps
    for n in xrange(1, n+1): # compute up to and including nth step
        # initialize probabilities to zero
        state_prob = [0 for i in xrange(num_states)]

        for state in xrange(num_states):
            for (tran_state, tran_prob) in transitions[state]:
                state_prob[state] += oldstate_prob[tran_state] * tran_prob
        oldstate_prob = state_prob
        final_after.append(state_prob[-1])
#        print state_prob

    return final_after

# token is string searched for
# s_len is length of string being searched
# a_size is alphabet size
def substring_prob(token, s_len, a_size=256):
    t_len = len(token)
    transitions = [[] for i in xrange(t_len + 1)]

    # for now, assuming uniform distribution, and that we go back to initial
    # state after a mismatch (latter depends on search string)

    # match transitions
    for i in xrange(1, t_len + 1):
        transitions[i].append((i-1, 1/a_size))
    # self loop on final state
    transitions[t_len].append((t_len, 1))

    # mismatch transitions
    # track how many previous characters match prefix of the token
    prefix_len = 0
    for i in xrange(0, t_len-1):
        # running count of current overlap with prefix
        if token[i] == token[prefix_len]:
            prefix_len += 1
        else:
            prefix_len = 0

        # if the prefix is the whole string we've processed so far, a
        # a mismatch goes back to the beginning 
        if prefix_len == i+1:
            return_point = 0
        else:
            return_point = prefix_len

        # add the mismatch transitions
        # keep in mind that mismatched character may be able to match
        # the character after the return point
        if token[return_point] == token[i+1]: 
            transitions[return_point].append((i+1, (a_size-1)/a_size))
        else:
            # special case in binary, 
            # since there can only be 1 mismatch case
            if a_size == 2:
                transitions[return_point+1].append((i+1, (a_size-1)/a_size))
            else:
                transitions[return_point].append((i+1, (a_size-1)/a_size * \
                                                        (a_size-1)/a_size))
                transitions[return_point+1].append((i+1, (a_size-1)/a_size * \
                                                        1/a_size))
    # add in mismatch transition from state 0 to itself
    transitions[0].append((0, (a_size-1)/a_size))

# old mismatch transitions
#    for i in xrange(0, t_len): # no mismatch from state t
#        mismatch[0].append((i, (a_size-1)/a_size))
#    print transitions

    probabilities = fsm_prob(transitions, s_len)
    # sanity check
#    total = 0
#    for i in probabilities:
#        total += i
#    print total
    return probabilities

# seq_len is length of the subsequence
# str_len is length of string being searched
# a_size is alphabet size
def subseq_prob(seq_len, str_len, a_size=256):
    transitions = [[] for i in xrange(seq_len + 1)]

    # mismatch transitions all self-loop
    for i in xrange(0, seq_len):
        transitions[i].append((i, (a_size-1)/a_size))
    transitions[seq_len] = [(seq_len, 1)] # last state is a sink
    # match transitions progress one state
    for i in xrange(1, seq_len + 1):
        transitions[i].append((i-1, 1/a_size))

    probabilities = fsm_prob(transitions, str_len)
    return probabilities

def fixedgapstrings(s):
    i = 0
    if s.endswith(".*"):
        s = s[:-2]
    if s.startswith(".*"):
        i = 2

    while(True):
        nextdotstar = s.find(".*", i)
        if nextdotstar > 0:
            yield s[i:nextdotstar]
            i = nextdotstar + 2
        else:
            yield s[i:]
            break

def reorder_fixedgaps(s):
    fixedgap = re.compile(r'\.\{(?P<num>\d+)\}')

    gap_size = 0
    pos = 0
    # sum up the gap sizes
    while True:
        m = fixedgap.search(s, pos)
        if m == None:
            break
        gap_size += int(m.group("num"))
        pos = m.end()

    return (fixedgap.sub("", s), gap_size)

# sig supporting some regex functionality including
#   .*
#   .{n}
# but not
#   .{n,m}
#   |
# modeling as an ndfa for simplicity. assumes that transition probabilities
# are independent, which is false. seems to be a good estimate though.
def regex_prob(sig, str_len, a_size=256, stats=None, max_context=2):
    transitions = [[]]

    # implicit .* at the beginning
    if sig.startswith(".*"):
        sig = sig[2:]

    for fixedgapstring in fixedgapstrings(sig):
        (fixedgapstring, gapsize) = reorder_fixedgaps(fixedgapstring)
        add_substring(fixedgapstring, transitions, a_size, stats, max_context=max_context)
        for i in xrange(gapsize):
            prevstate=len(transitions)-1
            transitions.append([(prevstate, 1)])

    laststate=len(transitions)-1
    transitions[laststate].append((laststate, 1))
#    print_transitions(transitions)
    return fsm_prob(transitions, str_len)

# same as regex_prob, but for a literal token.
def token_prob(sig, str_len, a_size=256, stats=None, max_context=2):
    transitions = [[]]

    add_substring(sig, transitions, a_size, stats, max_context=max_context)

    laststate=len(transitions)-1
    transitions[laststate].append((laststate, 1))
#    print_transitions(transitions)
    return fsm_prob(transitions, str_len)
#    fixedgap = re.compile(r'(?P<num>\d+)\}')
#    while(i < len(sig)):
#        prevstate = len(transitions) - 1
#
#        if sig.startswith(".*", i):
#            i += 2 
#            if prevstate >= 0:
#                transitions.append([(prevstate, 1), (prevstate+1, 1)])
#            else:
#                transitions.append([(0, 1)])
#        elif sig.startswith(".{", i):
#            i += 2
#            m = fixedgap.match(sig, i)
#            if m == None:
#                raise ValueError
#            i = m.end("num") + 1 # point i to character after }
#
#            # add a state for each character in the gap
#            for j in xrange(int(m.group("num"))):
#                transitions.append([(prevstate, 1)])
#                prevstate += 1
#        else:
#            i += 1
#            transitions.append([(prevstate, 1/a_size)])
#
#    # add self loop to final state
#    laststate = len(transitions) - 1
#    transitions[laststate].append((laststate, 1))
#
#    probabilities = fsm_prob(transitions, str_len)
#    return probabilities
#
#
##    for i in xrange(len(sig)):
##        transitions.append([(i, 1/a_size)])
##
##    transitions[len(sig)].append((len(sig), 1))
##    print transitions
##
##    probabilities = fsm_prob(transitions, str_len)
##    return probabilities

def graph_fsm(fsm, token):
    import pydot
    import re
    graph = pydot.Dot()

    # add states (nodes)
    for i in xrange(len(fsm)):
        if i == 0:
            label = 'init'
        else:
            label = re.escape(token[i-1].__repr__())
        n = pydot.Node(i, label=label)
        graph.add_node(n)

    # add transitions
    for state in xrange(len(fsm)):
#        for (prevstate, prob) in fsm[state]:
        (prevstate, prob) = fsm[state][0]
        graph.add_edge(pydot.Edge(prevstate, state, label='%f' % prob))

    return graph
