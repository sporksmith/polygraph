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

                
                # add in the best for each workload, 
                # and then the sum of the rest
                to_delete = []
                for work in workloads:
                    this_sigs.sort(lambda x,y: cmp(x['fn'][work['fname']], y['fn'][work['fname']]))
#                    print work['fname'], this_sigs[0]['fn'][work['fname']], this_sigs[-1]['fn'][work['fname']]
                    if not to_delete.count(this_sigs[0]):
                        sigs[x][alg.fname][trial].append(this_sigs[0])
                        to_delete.append(this_sigs[0])
                # delete the 'best' signatures
                for s in to_delete:
                    this_sigs.remove(s)

                if len(this_sigs) == 0:
                    continue

                # sum the fp of the rest of the signatures
                sum = 0
                for s in this_sigs:
                    sum += s['fp']
                sigs[x][alg.fname][trial].append({'fp': sum, 'fn': {}})
                for work in workloads:
                    sigs[x][alg.fname][trial][-1]['fn'][work['fname']] = max([s['fn'][work['fname']] for s in this_sigs])

            # sort the trials by sum of false positives
            def fp_sum(l):
                sum = 0
                fnsum = 0
                for s in l:
                    sum += s['fp']
                for work in workloads:
                    fnsum += min([s['fn'][work['fname']] for s in l])
                return sum + fnsum 
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
#    result.append('\\begin{table*}\n')
#    result.append('\\begin{center}\n')
    result.append('\\begin{tabular}{|c|')
    result.append(('|c' * (len(workloads)+1) + '|') * len(algorithms))
    result.append('}\\hline\n')
    
    # Algorithm names along the top
    for i in xrange(len(algorithms)):
        if i < len(algorithms)-1:
            result.append('& \multicolumn{%d}{c||}{%s} ' % (1+len(workloads), algorithms[i].pname))
        else:
            result.append('& \multicolumn{%d}{c|}{%s} ' % (1+len(workloads), algorithms[i].pname))
    result.append(r'\\' + '\n')
    result.append('\\hline\n')
    result.append('Samples ')
    result.append(('& False Pos ' + '& False Neg' * len(workloads)) * len(algorithms)) 
    result.append(r'\\' + '\n')
    result.append('\\hline\n')

    for x in xs:
        result.append('%d ' % x)
        for alg in algorithms:
            result.append(" & \\begin{tabular}{c}")
            for sig in sigs[x][alg.fname][numtrials//2]:
                result.append("%f" % sig['fp'])
                result.append(r"\\")
            result.pop() # get rid of last line break
            result.append("\\end{tabular}")
            for work in workloads:
                if work['numeval'] > 0:
                    result.append(" & \\begin{tabular}{c}")
                    for sig in sigs[x][alg.fname][numtrials//2]:
                        result.append("%f" % sig['fn'][work['fname']])
                        result.append(r"\\")
                    result.pop() # get rid of last line break
                    result.append("\\end{tabular}")
        result.append(r'\\' + '\n')
        result.append('\\hline\n')

#    result.append('\\hline\n')
    result.append('\\end{tabular}\n')
#    result.append('\\caption{%s}\n' % caption)
#    result.append('\\end{center}\n')
#    result.append('\\end{table*}\n')

    return ''.join(result)
