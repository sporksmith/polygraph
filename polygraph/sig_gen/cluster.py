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
import sets
import polygraph.trace_crunching.stream_trace as stream_trace

# clusters are dictionaries with keys:
# 'samples' = []	list of incoorporated sample indices
# 'sig' = ?		signature for this cluster
# 'sig_score'
# 'left' = cluster
# 'right' = cluster
# 'cb_data' = {}    dictionary for callbacks to add their own data

def graph_clusters(clusters):
    """Use dot to show clustering tree."""

    import pydot
    graph = pydot.Dot()

    def add_cluster(c):
        print c['index']
        n = pydot.Node(c['index'], label='coverage %d\\nscore %d' % (len(c['samples']), c['sig_score']))
        graph.add_node(n)
        if c['left']:
            add_cluster(c['left'])
            add_cluster(c['right'])
            graph.add_edge(pydot.Edge(c['left']['index'], c['index']))
            graph.add_edge(pydot.Edge(c['right']['index'], c['index']))

    for c in clusters:
        add_cluster(c)

    return graph

def backtrack(max_fp_count, fpos_training_streams, cluster, min_cluster_size):
    """
    If false positive rate of cluster exceeds max_fp_count, undo the
    the last merge and call 'backtrack' on both resulting clusters.
    """

    if len(cluster['samples']) < min_cluster_size:
        return [cluster]

    st = stream_trace.StreamTrace(fpos_training_streams)
    count = 0
    sample = st.next()
    while (sample):
        if cluster['sig'].match(sample):
            count += 1
            if count > max_fp_count: break
        sample = st.next()
    else:
        # fp rate was low. no need to backtrack
        print "Cluster OK"
        return [cluster]

    # fp rate was too high. unmerge, and backtrack each child
    print "Splitting cluster"
    st = None
    rv = backtrack(max_fp_count, fpos_training_streams, cluster['left'], min_cluster_size)
    rv.extend(backtrack(max_fp_count, fpos_training_streams, cluster['right'], min_cluster_size))
    return rv

def cluster(sig_generation_cb, min_score, samples, bound_similarity=False, cluster_seeds=None, max_fp_count=None, fpos_training_streams=None, min_cluster_size=3):
    """
    Perform hierarchical clustering.

    Parameters:
    sig_generation_cb
    min_score
    samples
    bound_similarity=True
    cluster_seeds=None
    max_fp_count=None
    fpos_training_streams=None
    min_cluster_size=3
    """

    clusters = [] # sequence of all clusters
    cluster_pairs = [] # sequence of potential merges, sorted by score
    unmerged_clusters = sets.Set(range(len(samples)))

    # initialize clusters
    for i in xrange(len(samples)):
        cluster = {'samples': [i],
                   'index': i,
                   'sig': None,
                   'sig_score': 0,
                   'left': None,
                   'right': None,
                   'cb_data': {},
        }
        clusters.append(cluster)

    # compute merge scores
    if not cluster_seeds:
        cluster_seeds = range(len(clusters))
    print "*" * 10, "Comparing all sample pairs", "*" * 10
    for i in cluster_seeds:
        for j in xrange(i+1, len(clusters)):
            (sig, score) = sig_generation_cb(clusters[i], clusters[j])
            print i,j,score,
            if score >= min_score:
                cluster_pairs.append({'left': i, 'right': j,'score': score, 'sig': sig})
                print "added to merge pool"
            else:
                print "too low; not added"

    cluster_pairs.sort(lambda x,y: cmp(x['score'], y['score']))

    # it's merge time!
    print "*" * 10, "Merging Clusters", "*" * 10

    while len(cluster_pairs) > 0 and len(unmerged_clusters) > 1:
        # get next best pair
        pair = cluster_pairs.pop()
        left_i = pair['left']
        right_i = pair['right']
        left = clusters[left_i]
        right = clusters[right_i]

        # if either has already been merged, get the next one
#            if left_i not in unmerged_clusters or right_i not in unmerged_clusters:
#                continue

        print left_i, right_i, 

        # if we already generated the signature, use it.
        if pair['sig'] != None:
            new_sig = pair['sig']
            new_score = pair['score']
            print new_score,
        # if we only bounded the merge score, generate the signature,
        # compute the actual score, and determine if this is still
        # the best current merge
        else:
            (new_sig, new_score) = sig_generation_cb(clusters[pair['left']], clusters[pair['right']])
            print new_score,

            if new_score < min_score:
                print "too low; dropped"
                continue
            if len(cluster_pairs) > 0 and new_score < cluster_pairs[-1]['score']:
                pair['sig'] = new_sig
                pair['score'] = new_score
                cluster_pairs.append(pair)
                cluster_pairs.sort(lambda x,y: cmp(x['score'], y['score']))
                print "not best current merge; back into merge pool"
                continue

        new_cluster = {'samples': left['samples'] + right['samples'],
                       'index': len(clusters),
                       'sig': new_sig,
                       'sig_score': new_score,
                       'left': left,
                       'right': right,
                       'cb_data': {},
                      }
        clusters.append(new_cluster)
        print '-->', new_cluster['index']
        unmerged_clusters.remove(left_i)
        unmerged_clusters.remove(right_i)
        unmerged_clusters.add(new_cluster['index'])

        # figure out which pairs need to be deleted, and what new
        # pairs should be computed
        pairs_to_delete = []
        merges_to_compute = {}
        for i in xrange(len(cluster_pairs)):
            if cluster_pairs[i]['left'] == left_i or cluster_pairs[i]['left'] == right_i: 
                pairs_to_delete.append(i)
                if merges_to_compute.has_key(cluster_pairs[i]['right']):
                    merges_to_compute[cluster_pairs[i]['right']] = \
                    min(merges_to_compute[cluster_pairs[i]['right']], cluster_pairs[i]['score'])
                else:
                    merges_to_compute[cluster_pairs[i]['right']] = \
                    cluster_pairs[i]['score']
            if cluster_pairs[i]['right'] == left_i or cluster_pairs[i]['right'] == right_i:
                pairs_to_delete.append(i)
                if merges_to_compute.has_key(cluster_pairs[i]['left']):
                    merges_to_compute[cluster_pairs[i]['left']] = \
                    min(merges_to_compute[cluster_pairs[i]['left']], cluster_pairs[i]['score'])
                else:
                    merges_to_compute[cluster_pairs[i]['left']] = \
                    cluster_pairs[i]['score']

        # delete the invalid pairs
        pairs_to_delete.reverse()
        for i in pairs_to_delete:
            del cluster_pairs[i]
                
        # compute merge pairs for new cluster
        for i in merges_to_compute.keys():
            if bound_similarity:
                score = merges_to_compute[i]
                sig = None
            else:
                (sig, score) = sig_generation_cb(clusters[i], new_cluster)
            print new_cluster['index'],i,score,
            if score >= min_score:
                cluster_pairs.append({'left': i, 
                                      'right': new_cluster['index'],
                                      'score': score, 'sig': sig})
                print "added to merge pool"
            else:
                print "too low; not added"

        # re-sort pairs
        cluster_pairs.sort(lambda x,y: cmp(x['score'], y['score']))


    # measure false positives in training data and unmerge as necessary
    roots = []
    if fpos_training_streams:
        for cluster in unmerged_clusters:
            roots.extend(backtrack(max_fp_count, fpos_training_streams, clusters[cluster], min_cluster_size))
    else:
        for i in unmerged_clusters:
            roots.append(clusters[i])
    return roots
