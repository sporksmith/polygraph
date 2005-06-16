#!/usr/bin/env python
from __future__ import generators
from __future__ import division
import string
import sys
import time
import os
import random

def fpos_eval_trace(sig, maxnum, streamfile):
    """Evaluate false positives in a trace of innocuous flows."""

    import polygraph.trace_crunching.stream_trace

    fpos = 0
    count = 0
    s = polygraph.trace_crunching.stream_trace.StreamTrace(streamfile)

    stream = s.next()
    while (stream):
        count += 1
        if sig.match(stream):
            fpos += 1
        stream = s.next()
        if count == maxnum:
            break

    return (fpos, count)

def fpos_eval_usrbin(sig, maxsize=100000000):
    """
    Evaluate false positives in program binaries.

    Used to see if signatures for obfuscated shellcode can distinguish between
    obfuscated shellcode and other executable strings.
    """

    trial_count = 0
    fpos_count = 0

    # iterate through file list
    for f in os.listdir("/usr/bin/"):
        # read up to maxsize bytes of each file
        try:
            sample = open("/usr/bin/%s" % f).read(maxsize)
        except IOError:
            continue

        # only use binary programs, not scripts, etc.
        if sample.find('ELF') < 0:
            continue

        # see if the signature matches
        trial_count += 1
        if sig.match(sample):
            fpos_count += 1

    return (fpos_count, trial_count)

def evaluate(sigs, variable_workload, fixed_workloads, var_range, fpos_eval_cb, trials=1, starttrial=0):
    """
    Generate and evaluate signatures.

    In each trial, the suspicious pool is made up of samples from
    variable_workload and fixed_workloads. Each workload could be, for
    example, a different worm, or a noise source.
    (The innocuous pool is specified when creating the signature objects)

    Parameters:
    sigs -- sequence of signature objects
    variable_workload -- a dictionary describing the variable size workload
    fixed_workloads -- a sequence of workload dictionaries
    var_range -- a sequence of how many samples to use from variable_workload
    fpos_eval_cb -- function to evaluate false positives
    trials -- number of trials to run
    starttrial -- which trial # to start on. Useful for distributing execution
                  of each trial.
    """


    import time
    import sys
    timestamp = int(time.time())
    os.mkdir(str(timestamp))

    # both print and log the output, to easily monitor
    # current progress of experiments
    logfile = open('%d.logfile' % timestamp, 'w')
    def logwrite(str): 
        sys.stdout.write(str)
        logfile.write(str)
        sys.stdout.flush()
        logfile.flush()

    logwrite("Sig Algorithm; Size; Time; Fpos; Fneg; Fneg_train; signature\n")

    # cache of signature false positive rates.
    # common case is that most trials will generate the 'correct' signature.
    # No sense in reevaluating false positives every time for the same sig.
    fpos_cache = {}

    # current offset into variable workload
    offset = starttrial * sum(var_range)

    for trial in xrange(starttrial, trials):
        for pool_size in var_range:
            # build suspicious pool
            training_set = variable_workload['train'][offset:offset+pool_size]
            offset += pool_size
            for w in fixed_workloads:
                training_set.extend(w['train'][trial*w['numtrain']:(trial+1)*w['numtrain']])
            random.shuffle(training_set)

            # limit sample length to 10k FIXME
            for s in xrange(len(training_set)):
                if len(training_set[s]) > 10000:
                    training_set[s] = training_set[s][:10000]

            for sig in sigs:
                # make sure key exists in fpos cache
                if not fpos_cache.has_key(sig.fname):
                    fpos_cache[sig.fname] = {}

                # Generate signature
                t0 = time.time()
                cluster_sigs = sig.train(training_set)
                t1 = time.time()
#                ans = 'z'
#                while True:
#                    try:
#                        t0 = time.time()
#                        cluster_sigs = sig.train(training_set)
#                        t1 = time.time()
#                    except Exception, e:
#                        print str(e)
#                        ans = 'z'
#                        while ans[0] != 'n' and ans[0] != 'r':
#                            print "(r)etry or (n)ext?"
#                            ans = sys.stdin.readline()
#                        if ans[0] == 'n':
#                            logwrite("%s; %d; except: %s: %s skip\n" % (sig.pname, pool_size, type(e), str(e))) 
#                            break
#                        if ans[0] == 'r':
#                            logwrite("%s; %d; except: %s: %s retry\n" % (sig.pname, pool_size, type(e), str(e))) 
#                    else:
#                        break
#                if ans[0] == 'n':
#                    continue
                deltat = t1-t0

                # prefix for logfiles
                prefix = '%d/%s' % (timestamp, sig.fname)

                # dump the overall signature to a file for posterity
                # XXX disabled, these can get large because its the whole
                # signature object. Human readable signature is printed to
                # log file anyways.
#                import cPickle
#                f = open('%s.sig.%d.pickle.%d' % (prefix, pool_size, trial), 'w')
#                cPickle.dump(sig, f, cPickle.HIGHEST_PROTOCOL)
#                f.close()

                # log how long signature took to generate
                f = open('%s.deltat.%d' % (prefix, trial), 'a')
                f.write('%d\t%f\n' % (pool_size, deltat))
                f.close()

                # test and report each generated signature
                for csig in cluster_sigs:
                    # test for false negatives in training set
                    fnegs_train = 0
                    for sample in training_set:
                        if not csig.match(sample):
                            fnegs_train += 1

                    # test for false negatives in eval sets
                    fnegs = {}
                    for workload in [variable_workload] + fixed_workloads:
                        fnegs[workload['fname']] = 0
                        for sample in workload['eval']:
                            if not csig.match(sample):
                                fnegs[workload['fname']] += 1

                    # test for false positives
                    # (first check if we've already generated this sig)
#                    if fpos_cache[sig.fname].has_key(str(csig)):
#                        (fpos, num_fpos_eval) = fpos_cache[sig.fname][str(csig)]
#                    else:
                    (fpos, num_fpos_eval) = fpos_eval_cb(csig)
#                        fpos_cache[sig.fname][str(csig)] = (fpos, num_fpos_eval)

                    # print results for this trial
                    logwrite("%s; %d; %f; %d/%d; [%s]/[%s]; %d/%d; %s\n" % \
                        (sig.pname, pool_size, 
                        deltat,
                        fpos, num_fpos_eval, 
                        ''.join(['%d,' % fnegs[w['fname']] for w in [variable_workload] + fixed_workloads]),
                        ''.join(['%d,' % len(w['eval']) for w in [variable_workload] + fixed_workloads]),
                        fnegs_train, len(training_set), 
                        str(csig)))
                    sys.stdout.flush()

                    if num_fpos_eval > 0:
                        f = open('%s.fpos.%d' % (prefix, trial), 'a')
                        f.write('%d\t%f\n' % (pool_size, fpos / num_fpos_eval))
                        f.close()

                    for w in [variable_workload] + fixed_workloads:
                        if len(w['eval']) > 0:
                            f = open('%s.fneg.%s.%d' % (prefix, w['fname'], trial), 'a')
                            f.write('%d\t%f\n' % (pool_size, fnegs[w['fname']] / len(w['eval'])))
                            f.close()

                # Uncomment to graph the hierarchical clustering
#                try:
#                    import polygraph.sig_gen.cluster
#                    clusters = sig.clusters
#                    graph = polygraph.sig_gen.cluster.graph_clusters(clusters)
#                    graph.write_fig('%s.%d.%d.fig' % (prefix, pool_size, trial), prog='dot')
#                except AttributeError, ImportError:
#                    pass


def bigeval(
    sig_names=None,         #list of strings
    training_streams=None,  #filename
    training_stats=None,    #stats filename
    fpos_eval_streams=None, #filename
    fpos_eval_count=None,   #int
    dynamic_workload=None,  #workload
    static_workloads=None,  #list of workloads
    dynamic_range=None,     #list of sizes for dynamic workload
    trials=None,            # number of trials
    starttrial=0,
    do_table=False,             # this is a horrible hack.
    ts=None,
    caption="No caption"
    ):
    """
    A wrapper to 'evaluate' that creates the signature objects.

    Parameters:
    sig_names         -- sequence of strings indicating what 
                         signature types to use
    training_streams  -- filename of streamfile of innocuous pool
    training_stats    -- filename of statistics of innocuous pool
    fpos_eval_streams -- filename of streamfile to evaluate false positives
    fpos_eval_count   -- how many streams to evaluate each signature on
    dynamic_workload  -- a dictionary describing the variable size workload
    static_workloads  -- a sequence of workload dictionaries
    dynamic_range     -- sequence of sizes for dynamic workload
    trials            -- number of trials to run
    starttrial        -- which trial to start on. 
                         Useful for distributing execution of each trial.
    do_table          -- Set to true to generate table of results 
                         (this is a horrible hack)
    ts                -- If generating a table, this is the 
                         ts for which results to use
    caption           -- If generating a table, this will be the table caption
    """

    import pickle

    stats=None
    if not do_table:
        # load the training stats
        if training_stats:
            print "Loading training stats"
            f = open(training_stats)
            stats = pickle.load(f)
        else:
#            print "No training stats"
            stats=None

        # load the workloads
        for workload in static_workloads + [dynamic_workload]:
            # load from pickle file
            print "Loading workload %s" % workload['pickle']
            f = open(workload['pickle'])
            samples = pickle.load(f)

            # use some of the samples for false negative evaluation
            workload['eval'] = samples[:workload['numeval']]
            assert(len(workload['eval']) == workload['numeval'])
            del samples[:workload['numeval']]
            workload['train'] = samples

        # make sure the training pools are big enough
        del dynamic_workload['train'][sum(dynamic_range)*trials:]
        print len(dynamic_workload['train']), sum(dynamic_range)*trials
        assert(len(dynamic_workload['train']) >= sum(dynamic_range)*trials)
        for workload in static_workloads:
            del workload['train'][workload['numtrain']*trials:]
            assert(len(workload['train']) >= (workload['numtrain']*trials))

    # initialize the signatures
#    print "Initializing signatures"
    sigs = []
    for n in sig_names:
        if n == 'LCS':
            import polygraph.sig_gen.lcs
            sigs.append(polygraph.sig_gen.lcs.LCS(pname="Longest Substring", fname="LCS"))
        elif n == 'BayesAnd':
            import polygraph.sig_gen.bayes
            sigs.append(polygraph.sig_gen.bayes.Bayes(pname="Conjunction", fname="BayesAnd", kfrac=1,minlen=2,statsfile=stats, training_trace=training_streams, threshold_style='min'))
        elif n == 'BayesFuzzyAnd':
            import polygraph.sig_gen.bayes
            sigs.append(polygraph.sig_gen.bayes.Bayes(pname="BayesFuzzyAnd", fname="BayesFuzzyAnd", kfrac=1,minlen=2,statsfile=stats, threshold_style='bound', max_fpos=5,training_trace=training_streams))
        elif n == 'LCSeq':
            import polygraph.sig_gen.lcseq_tree
            sigs.append(polygraph.sig_gen.lcseq_tree.LCSeqTree(pname="Token Subsequence", fname="lcseq", kfrac=1, tokenize_all=True, tokenize_pairs=False, minlen=2,statsfile=stats, do_cluster=False))
        elif n == 'Bayes2':
            import polygraph.sig_gen.bayes
            sigs.append(polygraph.sig_gen.bayes.Bayes(pname="Bayes2", fname="bayes2", kmin=4, kfrac=.2,minlen=2,statsfile=stats, threshold_style='bound', max_fpos=5, training_trace=training_streams))
        elif n == 'Bayes':
            import polygraph.sig_gen.bayes
            sigs.append(polygraph.sig_gen.bayes.Bayes(pname="Bayes", fname="bayes", kmin=3, kfrac=.2,minlen=2,statsfile=stats, threshold_style='bound', max_fpos=5, training_trace=training_streams))
        elif n == 'LCSeqTree':
            import polygraph.sig_gen.lcseq_tree
            sigs.append(polygraph.sig_gen.lcseq_tree.LCSeqTree(pname="Token Subsequence", fname="lcseq_tree", k=3, tokenize_all=True, tokenize_pairs=False, minlen=2,statsfile=stats, spec_threshold=3, max_fp_count=5, fpos_training_streams=training_streams, min_cluster_size=3))
        elif n == 'BayesAndTree':
            import polygraph.sig_gen.bayes_tree
            sigs.append(polygraph.sig_gen.bayes_tree.BayesTree(pname="Conjunction", fname="BayesAndTree", kfrac=1,minlen=2,statsfile=stats, threshold_style='min', spec_threshold=3, max_fp_count=5, fpos_training_streams=training_streams, min_cluster_size=3))
        elif n == 'BayesAndTree2':
            import polygraph.sig_gen.bayes_tree
            sigs.append(polygraph.sig_gen.bayes_tree.BayesTree(pname="Conjunction2", fname="BayesAndTree2", kfrac=1,minlen=2,statsfile=stats, threshold_style='min', spec_threshold=3, max_fp_count=5, fpos_training_streams=training_streams, min_cluster_size=10))
        elif n == 'BayesFuzzyAndTree':
            import polygraph.sig_gen.bayes_tree
            sigs.append(polygraph.sig_gen.bayes_tree.BayesTree(pname="BayesFuzzyAndTree", fname="BayesFuzzyAndTree", kfrac=1,minlen=2,statsfile=stats, threshold_style='bound', spec_threshold=3, max_fp_count=5, fpos_training_streams=training_streams, min_cluster_size=3))
        elif n == 'BayesTree':
            import polygraph.sig_gen.bayes_tree
            sigs.append(polygraph.sig_gen.bayes_tree.BayesTree(pname="Bayes", fname="bayes_tree", kmin=3, kfrac=.2,minlen=2,statsfile=stats, threshold_style='bound', spec_threshold=3, max_fp_count=5, fpos_training_streams=training_streams, min_cluster_size=3))
        else:
            print "Bad signature name"
            sys.exit(1)

    # run the evaluation
    if not do_table:
        if fpos_eval_streams:
            evaluate(sigs, dynamic_workload, static_workloads, dynamic_range, lambda s: fpos_eval_trace(s, fpos_eval_count, fpos_eval_streams), trials, starttrial)
        else:
            evaluate(sigs, dynamic_workload, static_workloads, dynamic_range, lambda s: fpos_eval_usrbin(s), trials, starttrial)
    else:
        import make_graph as make_table
#        import make_table_multiple2 as make_table
#        import make_table
        print make_table.make_table(sigs, [dynamic_workload] + static_workloads, ts, dynamic_range, numtrials=trials, caption=caption)
