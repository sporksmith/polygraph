#!/usr/bin/env python

from __future__ import division

def median(l):
    l = l[:]
    l.sort()
    return l[len(l)/2]

def get_data(prefix, numtrials=5):
    data =[]
    for trial in xrange(numtrials):
        f = open('%s.%d' % (prefix,trial))
        data.append({})
        for line in f.xreadlines():
            (x,y) = line.split()
            x = int(x)
            y = float(y)
            if not data[trial].has_key(x):
                data[trial][x] = []
            data[trial][x].append(y)
    return data

# algorithms = list of {'pname': '', 'fname': ''}
# workloads = list of {'pname': '', 'fname': ''}
def make_table(algorithms, all_workloads, ts, xs, numtrials=5, caption="No caption"):
    workloads = []
    for w in all_workloads:
        if w['numeval'] > 0:
            workloads.append(w)

#    if ts:
#        ts = ts + '.'
#    else:
#        ts = ''
#    print ts




    # get the false positive and negatives
    data = {}
    for alg in algorithms:
        data[alg.fname] = {}
        data[alg.fname]['fp'] = get_data('%s.fpos' % alg.fname)

        data[alg.fname]['fn'] = {}
        for work in workloads:
            if work['numeval'] > 0:
                data[alg.fname]['fn'][work['fname']] = get_data('%s.fneg.%s' % (alg.fname, work['fname']))

#    print data['lcseq_tree']['fp'][0][0]

    # rearrange the data
    sigs = {}
    for x in xs:
        sigs[x] = {}
        for alg in algorithms:
            sigs[x][alg.fname] = []
            for trial in xrange(numtrials):
                sigs[x][alg.fname].append([])

                this_sigs = []
                for fp in data[alg.fname]['fp'][trial][x]:
                    this_sigs.append({'fp': fp, 'fn': {}})
                for work in workloads:
                    for fni in xrange(len(data[alg.fname]['fn'][work['fname']][trial][x])):
                        this_sigs[fni]['fn'][work['fname']] = data[alg.fname]['fn'][work['fname']][trial][x][fni]

                
                # delete the best sig for each workload
                to_delete = []
                for work in workloads:
                    this_sigs.sort(lambda x,y: cmp(x['fn'][work['fname']], y['fn'][work['fname']]))
                    if not to_delete.count(this_sigs[0]):
#                        to_delete.append(this_sigs[0].copy())
#                        sigs[x][alg.fname][trial].append(this_sigs[0].copy())
#                        print sigs[x][alg.fname][trial][-1]['fn']
#                        if sum(sigs[x][alg.fname][trial][-1]['fn'].values()) < 0.1:
                        if this_sigs[0]['fn'][work['fname']] < 0.1:
                            this_sigs[0]['fp'] = 0
#                            sigs[x][alg.fname][trial][-1]['fp'] = 0
                # delete the 'best' signatures
#                for s in to_delete:
#                    this_sigs.remove(s)

                if len(this_sigs) == 0:
                    continue

                # sum the fp of the rest of the signatures
                fpsum = 0
                for s in this_sigs:
                    fpsum += s['fp']
#                sigs[x][alg.fname][trial][-1]['fp'] = fpsum
                sigs[x][alg.fname][trial].append({'fp': fpsum, 'fn': {}})

            # sort the trials by sum of false positives
            def fp_sum(l):
                sum = 0
                fnsum = 0
                for s in l:
                    sum += s['fp']
#                for work in workloads:
#                    fnsum += min([s['fn'][work['fname']] for s in l])
                return sum# + fnsum 
            sigs[x][alg.fname].sort(lambda a,b: cmp(fp_sum(a), fp_sum(b)))
#            if alg.fname == 'lcseq_tree' and x == 20:
#                for s in sigs[x][alg.fname]:
#                    print s
#                return ''

#    for trial in sigs[30]['lcseq_tree']:
#        print trial
#    return



    # build the table
    result = []
   
    # Open a file for each algorithm
    files = {}
    for alg in algorithms:
        files[alg] = open(alg.fname + '.addtlfpos', 'w')

    # For each x value
    for x in xs:
        # For each algorithm
        for alg in algorithms:
            # use 95th percentile... if we actually had that many trials
            for sig in sigs[x][alg.fname][int(numtrials*.95)-1]:
                # write to file
                files[alg].write('%d\t%f\n' % (x, sig['fp']))
#                result.append("%f" % sig['fp'])

