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

def median(l):
    l = l[:]
    l.sort()
    return l[len(l)/2]

def get_data(prefix, numtrials=1):
    data = [{}] * numtrials
    for trial in xrange(numtrials):
        f = open('%s.%d' % (prefix,trial))
        for line in f.xreadlines():
            (x,y) = line.split()
            x = int(x)
            y = float(y)
            if not data[trial].has_key(x):
                data[trial][x] = []
            data[trial][x].append(y)
    return data[trial]

# algorithms = list of {'pname': '', 'fname': ''}
# workloads = list of {'pname': '', 'fname': ''}
def make_table(algorithms, all_workloads, ts, xs):
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
        data[alg] = {}
        data[alg]['fp'] = get_data('%s.fpos' % alg.fname)

        data[alg]['fn'] = {}
        for work in workloads:
            if work['numeval'] > 0:
                data[alg]['fn'][work['fname']] = get_data('%s.fneg.%s' % (alg.fname, work['fname']))

    # build the table
    result = []
    result.append('\\begin{table*}\n')
    result.append('\\begin{center}\n')
    result.append('\\begin{tabular}{|c|')
    result.append(('|c' * (len(workloads)+1) + '|') * len(algorithms))
    result.append('}\\hline\n')
    
    # Algorithm names along the top
    for i in xrange(len(algorithms)):
        if i < len(algorithms)-1:
            result.append('& \multicolumn{2}{c||}{%s} ' % algorithms[i].pname)
        else:
            result.append('& \multicolumn{2}{c|}{%s} ' % algorithms[i].pname)
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
            for signum in xrange(len(data[alg]['fp'][x])):
                result.append("%f" % data[alg]['fp'][x][signum])
                result.append(r"\\")
            result.pop() # get rid of last line break
            result.append("\\end{tabular}")
            for work in workloads:
                if work['numeval'] > 0:
                    result.append(" & \\begin{tabular}{c}")
                    for signum in xrange(len(data[alg]['fn'][work['fname']][x])):
                        result.append("%f" % data[alg]['fn'][work['fname']][x][signum])
                        result.append(r"\\")
                    result.pop() # get rid of last line break
                    result.append("\\end{tabular}")
        result.append(r'\\' + '\n')
        result.append('\\hline\n')

#    result.append('\\hline\n')
    result.append('\\end{tabular}\n')
    result.append('\\end{center}\n')
    result.append('\\end{table*}\n')

    return ''.join(result)
